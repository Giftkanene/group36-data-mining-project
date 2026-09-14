"""Samfya Town Council scraper for UNZA CSC 4792 Group 36.

Outputs are pipe-separated CSV files. The script intentionally keeps data raw
so the cleaning workflow can perform standardisation and preprocessing.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
import csv
import re
import time
import hashlib
import warnings
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://www.samfyacouncil.gov.zm"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
DOWNLOAD_DIR = Path(__file__).resolve().parents[1] / "data" / "downloads"

RESOURCE_PAGES = {
    "community_projects": f"{BASE_URL}/?page_id=2029",
    "grants_and_loans": f"{BASE_URL}/?page_id=2097",
    "skills_and_bursaries": f"{BASE_URL}/?page_id=2078",
    "publications": f"{BASE_URL}/?page_id=195",
    "application_forms": f"{BASE_URL}/?page_id=1224",
}

NEWS_START_URLS = [
    f"{BASE_URL}/?cat=1",
    f"{BASE_URL}/?page_id=187",
]

ALLOWED_DOC_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".zip"
}

RESOURCE_COLUMNS = [
    "council", "category", "year_raw", "document_title_raw",
    "document_url", "file_type", "source_page", "retrieved_at_utc",
]

NEWS_COLUMNS = [
    "council", "title_raw", "published_date_raw", "excerpt_raw",
    "article_url", "source_listing_page", "article_text_raw",
    "linked_document_urls", "retrieved_at_utc",
]

@dataclass
class ScrapeConfig:
    delay_seconds: float = 1.0
    timeout_seconds: int = 30
    max_news_pages: int = 10
    download_documents: bool = False
    fetch_article_details: bool = True
    allow_insecure_tls_fallback: bool = True


def build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.mount("http://", HTTPAdapter(max_retries=retry))
    session.headers.update({
        "User-Agent": (
            "UNZA-CSC4792-Group36-SamfyaAcademicScraper/1.0 "
            "(public academic data collection; low request rate)"
        )
    })
    return session


def get_response(
    session: requests.Session,
    url: str,
    timeout: int = 30,
    stream: bool = False,
    allow_insecure_tls_fallback: bool = True,
) -> requests.Response:
    """Fetch an official resource, handling its current expired certificate.

    The Samfya site currently presents an expired TLS certificate. We always try
    normal certificate verification first. Only after that specific failure, and
    only for the configured official council domain, we retry without certificate
    verification so public, non-authenticated academic data remains accessible.
    """
    try:
        response = session.get(url, timeout=timeout, stream=stream)
    except requests.exceptions.SSLError:
        if not allow_insecure_tls_fallback or not is_same_domain(url):
            raise
        print(f"  WARNING: expired TLS certificate at {url}; retrying public resource without verification.")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", requests.packages.urllib3.exceptions.InsecureRequestWarning)
            response = session.get(url, timeout=timeout, stream=stream, verify=False)
    response.raise_for_status()
    return response


def get_soup(
    session: requests.Session,
    url: str,
    timeout: int = 30,
    allow_insecure_tls_fallback: bool = True,
) -> BeautifulSoup:
    response = get_response(
        session,
        url,
        timeout,
        allow_insecure_tls_fallback=allow_insecure_tls_fallback,
    )
    return BeautifulSoup(response.text, "html.parser")


def clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip()


def utc_timestamp() -> str:
    """Return a machine-readable retrieval timestamp for provenance."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def year_from_text(text: str) -> str:
    match = re.search(r"\b(20\d{2})\b", text)
    return match.group(1) if match else ""


def is_same_domain(url: str) -> bool:
    try:
        return urlparse(url).netloc.lower().endswith("samfyacouncil.gov.zm")
    except Exception:
        return False


def looks_like_document(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower()
    suffix = Path(path).suffix.lower()
    return (
        suffix in ALLOWED_DOC_EXTENSIONS
        or "/wp-content/uploads/" in path
    )


def infer_file_type(url: str) -> str:
    suffix = Path(urlparse(url).path).suffix.lower().lstrip(".")
    return suffix or "unknown"


def scrape_resource_page(
    session: requests.Session,
    category: str,
    page_url: str,
    timeout: int,
    allow_insecure_tls_fallback: bool,
) -> list[dict]:
    soup = get_soup(session, page_url, timeout, allow_insecure_tls_fallback)
    rows: list[dict] = []

    for anchor in soup.find_all("a", href=True):
        href = urljoin(page_url, anchor.get("href"))
        title = clean_text(anchor.get_text(" ", strip=True))
        if not title or not is_same_domain(href) or not looks_like_document(href):
            continue
        rows.append({
            "council": "Samfya Town Council",
            "category": category,
            "year_raw": year_from_text(title),
            "document_title_raw": title,
            "document_url": href,
            "file_type": infer_file_type(href),
            "source_page": page_url,
            "retrieved_at_utc": utc_timestamp(),
        })

    # Some WordPress pages wrap document links inside buttons/images whose visible
    # anchor text is weak. Keep the href and create a fallback title from filename.
    for row in rows:
        if len(row["document_title_raw"]) < 3:
            name = Path(urlparse(row["document_url"]).path).name
            row["document_title_raw"] = clean_text(re.sub(r"[-_]", " ", name))

    return rows


def deduplicate(records: list[dict], key: str) -> list[dict]:
    seen: set[str] = set()
    unique: list[dict] = []
    for record in records:
        value = record.get(key, "")
        if value and value not in seen:
            seen.add(value)
            unique.append(record)
    return unique


def scrape_resources(config: ScrapeConfig, session: requests.Session | None = None) -> list[dict]:
    session = session or build_session()
    records: list[dict] = []
    for category, url in RESOURCE_PAGES.items():
        print(f"[resources] {category}: {url}")
        try:
            records.extend(scrape_resource_page(
                session,
                category,
                url,
                config.timeout_seconds,
                config.allow_insecure_tls_fallback,
            ))
        except requests.RequestException as exc:
            print(f"  WARNING: failed to scrape {url}: {exc}")
        time.sleep(config.delay_seconds)

    return deduplicate(records, "document_url")


def extract_article_from_node(node, page_url: str) -> dict | None:
    heading = node.find(["h1", "h2", "h3", "h4"])
    anchor = heading.find("a", href=True) if heading else node.find("a", href=True)
    if not anchor:
        return None
    url = urljoin(page_url, anchor["href"])
    title = clean_text(anchor.get_text(" ", strip=True))
    if not title or not is_same_domain(url):
        return None

    text = clean_text(node.get_text(" ", strip=True))
    date_match = re.search(
        r"(?:Published\s+)?(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+20\d{2}",
        text,
        flags=re.I,
    )
    date_raw = date_match.group(0).replace("Published", "").strip() if date_match else ""
    excerpt = text
    if excerpt.lower().startswith(title.lower()):
        excerpt = clean_text(excerpt[len(title):])
    return {
        "council": "Samfya Town Council",
        "title_raw": title,
        "published_date_raw": date_raw,
        "excerpt_raw": excerpt[:2000],
        "article_url": url,
        "source_listing_page": page_url,
        "article_text_raw": "",
        "linked_document_urls": "",
        "retrieved_at_utc": utc_timestamp(),
    }


def scrape_article_detail(
    session: requests.Session,
    article_url: str,
    timeout: int,
    allow_insecure_tls_fallback: bool,
) -> tuple[str, str]:
    """Get full public article text and any linked council documents.

    Listing-page excerpts are often too short to describe a CDF project. Keeping
    the full raw text allows the cleaner to extract fields without revisiting the
    site, while the linked-document list preserves a traceable evidence trail.
    """
    soup = get_soup(session, article_url, timeout, allow_insecure_tls_fallback)
    content = soup.select_one("article .entry-content, .entry-content, .post-content")
    if content is None:
        content = soup.find("article") or soup
    text = clean_text(content.get_text(" ", strip=True))
    document_urls = sorted({
        urljoin(article_url, anchor["href"])
        for anchor in content.find_all("a", href=True)
        if is_same_domain(urljoin(article_url, anchor["href"]))
        and looks_like_document(urljoin(article_url, anchor["href"]))
    })
    return text[:20000], ";".join(document_urls)


def scrape_news_listing(
    session: requests.Session,
    url: str,
    timeout: int,
    allow_insecure_tls_fallback: bool,
) -> list[dict]:
    soup = get_soup(session, url, timeout, allow_insecure_tls_fallback)
    records: list[dict] = []
    for node in soup.find_all("article"):
        record = extract_article_from_node(node, url)
        if record:
            records.append(record)

    # Fallback for themes that do not use <article> elements.
    if not records:
        for heading in soup.find_all(["h2", "h3", "h4"]):
            anchor = heading.find("a", href=True)
            if not anchor:
                continue
            record = extract_article_from_node(heading.parent or heading, url)
            if record:
                records.append(record)
    return records


def scrape_news(config: ScrapeConfig, session: requests.Session | None = None) -> list[dict]:
    session = session or build_session()
    records: list[dict] = []

    # WordPress category pages are predictable and are the most reliable source
    # for pagination. Stop after the first empty page or configured maximum.
    for page_number in range(1, config.max_news_pages + 1):
        url = f"{BASE_URL}/?cat=1" if page_number == 1 else f"{BASE_URL}/?cat=1&paged={page_number}"
        print(f"[news] page {page_number}: {url}")
        try:
            page_records = scrape_news_listing(
                session,
                url,
                config.timeout_seconds,
                config.allow_insecure_tls_fallback,
            )
        except requests.RequestException as exc:
            print(f"  WARNING: failed to scrape {url}: {exc}")
            break
        if not page_records:
            break
        records.extend(page_records)
        time.sleep(config.delay_seconds)

    if config.fetch_article_details:
        for record in records:
            try:
                article_text, document_urls = scrape_article_detail(
                    session,
                    record["article_url"],
                    config.timeout_seconds,
                    config.allow_insecure_tls_fallback,
                )
                record["article_text_raw"] = article_text
                record["linked_document_urls"] = document_urls
            except requests.RequestException as exc:
                print(f"  WARNING: failed to retrieve article {record['article_url']}: {exc}")
            time.sleep(config.delay_seconds)

    return deduplicate(records, "article_url")


def safe_filename(url: str, fallback_title: str = "document") -> str:
    path_name = Path(urlparse(url).path).name
    if path_name and "." in path_name:
        base = path_name
    else:
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
        base = f"{fallback_title[:60]}-{digest}.bin"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", base)


def download_document(
    session: requests.Session,
    url: str,
    title: str,
    timeout: int,
    allow_insecure_tls_fallback: bool = True,
) -> Path | None:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    target = DOWNLOAD_DIR / safe_filename(url, title)
    try:
        with get_response(
            session,
            url,
            timeout,
            stream=True,
            allow_insecure_tls_fallback=allow_insecure_tls_fallback,
        ) as response:
            with target.open("wb") as fh:
                for chunk in response.iter_content(chunk_size=1024 * 128):
                    if chunk:
                        fh.write(chunk)
        return target
    except requests.RequestException as exc:
        print(f"  WARNING: download failed {url}: {exc}")
        return None


def save_pipe_csv(rows: list[dict], path: Path, fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=fieldnames,
            delimiter="|",
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def run(config: ScrapeConfig | None = None) -> tuple[list[dict], list[dict]]:
    config = config or ScrapeConfig()
    session = build_session()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    resources = scrape_resources(config, session)
    news = scrape_news(config, session)

    save_pipe_csv(
        resources,
        OUTPUT_DIR / "db-unza26-csc4792-samfya_resource_index.csv",
        RESOURCE_COLUMNS,
    )
    save_pipe_csv(
        news,
        OUTPUT_DIR / "db-unza26-csc4792-samfya_news.csv",
        NEWS_COLUMNS,
    )

    run_metadata = [{
        "run_at_utc": utc_timestamp(),
        "council": "Samfya Town Council",
        "resource_records": len(resources),
        "news_records": len(news),
        "resource_pages": ";".join(RESOURCE_PAGES.values()),
        "news_start_url": f"{BASE_URL}/?cat=1",
    }]
    save_pipe_csv(
        run_metadata,
        OUTPUT_DIR / "db-unza26-csc4792-samfya_scrape_run_metadata.csv",
        [
            "run_at_utc", "council", "resource_records", "news_records",
            "resource_pages", "news_start_url",
        ],
    )

    if config.download_documents and resources:
        for row in resources:
            path = download_document(
                session,
                row["document_url"],
                row["document_title_raw"],
                config.timeout_seconds,
                config.allow_insecure_tls_fallback,
            )
            row["downloaded_local_path"] = str(path) if path else ""
            time.sleep(config.delay_seconds)
        save_pipe_csv(
            resources,
            OUTPUT_DIR / "db-unza26-csc4792-samfya_resource_index.csv",
            RESOURCE_COLUMNS + ["downloaded_local_path"],
        )

    print(f"Saved {len(resources)} resource records and {len(news)} news records.")
    return resources, news


if __name__ == "__main__":
    run(ScrapeConfig(download_documents=False))
