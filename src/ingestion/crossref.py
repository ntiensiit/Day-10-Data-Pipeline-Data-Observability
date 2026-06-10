from __future__ import annotations

import dataclasses
from html import unescape
from dataclasses import dataclass
from pathlib import Path
import re
import time
import requests

from core.config import Settings
from core.utils import normalize_whitespace, write_json, read_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload into a list of PaperRecord.

    Rules:
    - Stable ID (DOI) must be present.
    - Title must be present.
    - Summary (abstract) must be present.
    - Remove HTML tags from abstract and normalize whitespace.
    - Extract authors, categories, published date, updated date, URLs.
    - Fill missing optional fields with empty strings or lists.
    - Drop records without stable ID, title, or summary.
    """
    items = payload.get("message", {}).get("items", [])
    records: list[PaperRecord] = []

    def parse_date(date_dict: dict | None) -> str:
        if not date_dict or not isinstance(date_dict, dict):
            return ""
        parts = date_dict.get("date-parts", [])
        if parts and isinstance(parts, list) and parts[0] and isinstance(parts[0], list):
            p = parts[0]
            if len(p) >= 3:
                return f"{p[0]:04d}-{p[1]:02d}-{p[2]:02d}"
            elif len(p) == 2:
                return f"{p[0]:04d}-{p[1]:02d}-01"
            elif len(p) == 1:
                return f"{p[0]:04d}-01-01"
        return ""

    for item in items:
        # 1. Extract DOI as paper_id
        paper_id = item.get("DOI", "").strip()

        # 2. Extract title (normally a list)
        title_list = item.get("title", [])
        title = ""
        if isinstance(title_list, list) and title_list:
            title = title_list[0]
        elif isinstance(title_list, str):
            title = title_list
        title = normalize_whitespace(title)

        # 3. Extract abstract/summary and strip HTML
        abstract = item.get("abstract", "") or ""
        abstract = re.sub(r"<[^>]+>", "", unescape(str(abstract)))
        summary = normalize_whitespace(abstract)

        # 4. Filter out invalid/empty records
        if not paper_id or not title or not summary:
            continue

        # 5. Extract authors
        authors: list[str] = []
        for author_dict in item.get("author", []):
            given = author_dict.get("given", "").strip()
            family = author_dict.get("family", "").strip()
            if given and family:
                name = f"{given} {family}"
            elif family:
                name = family
            elif given:
                name = given
            else:
                name = author_dict.get("name", "").strip()
            if name:
                authors.append(name)

        # 6. Extract subjects as categories
        categories = item.get("subject", [])
        if not isinstance(categories, list):
            categories = []
        categories = [normalize_whitespace(c) for c in categories if c]
        primary_category = categories[0] if categories else ""

        # 7. Extract dates
        published = ""
        for key in ["published-online", "published-print", "issued", "created"]:
            published = parse_date(item.get(key))
            if published:
                break

        updated = ""
        for key in ["indexed", "deposited"]:
            updated = parse_date(item.get(key))
            if updated:
                break
        if not updated:
            updated = published

        # 8. Extract URLs
        abs_url = item.get("URL", "").strip()
        pdf_url = ""
        links = item.get("link", [])
        if isinstance(links, list):
            for link in links:
                if isinstance(link, dict) and "application/pdf" in str(link.get("content-type", "")).lower():
                    pdf_url = link.get("URL", "").strip()
                    break

        # 9. Extract comment
        comment = item.get("comment", "")
        if isinstance(comment, list) and comment:
            comment = comment[0]
        comment = normalize_whitespace(str(comment)) if comment else ""

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment,
            )
        )

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch raw papers from Crossref, write JSON response, and return parsed PaperRecords."""
    url = "https://api.crossref.org/works"
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }
    headers = {"User-Agent": "Day10Lab/1.0 (mailto:student@example.com)"}

    max_retries = 3
    backoff = 2
    response = None
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            if response.status_code == 200:
                break
            elif response.status_code in {429, 500, 502, 503, 504}:
                time.sleep(backoff * (attempt + 1))
                continue
            else:
                response.raise_for_status()
        except requests.RequestException:
            if attempt == max_retries - 1:
                raise
            time.sleep(backoff * (attempt + 1))
    else:
        if response is not None:
            response.raise_for_status()
        else:
            raise RuntimeError("Failed to connect to Crossref API.")

    payload = response.json()
    write_json(settings.paths.raw_api_response, payload)
    records = parse_crossref_payload(payload)
    write_json(settings.paths.raw_records_json, [dataclasses.asdict(r) for r in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load and parse records from JSON snapshot back into PaperRecord objects."""
    data = read_json(path)
    return [PaperRecord(**item) for item in data]
