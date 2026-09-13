"""
Person B - Data Cleaner
Samfya Town Council (Group 36) cleaning pipeline.

Reads pipe-delimited raw CSVs from data/raw/ and writes pipe-delimited
cleaned CSVs to data/cleaned/. Idempotent: safe to re-run at any time.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "cleaned"
CLEAN.mkdir(parents=True, exist_ok=True)

SEP = "|"
ENCODING = "utf-8"


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------
_WS_RE = re.compile(r"\s+")


def norm_ws(value) -> str:
    """Trim + collapse internal whitespace. Returns '' for NaN/None."""
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    s = str(value).replace("\u00a0", " ")
    return _WS_RE.sub(" ", s).strip()


def clean_strings(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].map(norm_ws)
    return df


def read_raw(name: str) -> pd.DataFrame:
    """Read a raw pipe CSV with string-safe settings. Returns empty df if missing."""
    path = RAW / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep=SEP, dtype=str, keep_default_na=False, encoding=ENCODING)


def drop_exact_duplicates(df: pd.DataFrame, label: str, log: list) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    log.append(f"{label}: removed {before - len(df)} exact duplicate row(s).")
    return df


def add_index_column(df: pd.DataFrame, prefix: str = "R") -> pd.DataFrame:
    df = df.reset_index(drop=True)
    df.insert(0, "record_id", [f"{prefix}{i+1:04d}" for i in range(len(df))])
    return df


# ---------------------------------------------------------------------------
# Standardisation maps
# ---------------------------------------------------------------------------
STATUS_MAP = {
    "completed": "Completed", "complete": "Completed", "done": "Completed",
    "finished": "Completed",
    "in progress": "In progress", "in-progress": "In progress",
    "ongoing": "In progress", "on going": "In progress",
    "under construction": "In progress",
    "under procurement": "Under procurement", "procurement": "Under procurement",
    "tendering": "Under procurement",
    "deferred": "Deferred", "postponed": "Deferred", "stalled": "Deferred",
    "proposed": "Proposed", "planned": "Proposed", "not started": "Proposed",
    "": "Unknown", "unknown": "Unknown", "n/a": "Unknown", "na": "Unknown",
    "-": "Unknown",
}


def standardise_status(value: str) -> str:
    key = norm_ws(value).lower()
    return STATUS_MAP.get(key, "Unknown")


WARD_MAP = {
    "kapilibila": "Kapilibila",
    "samfya central": "Samfya Central",
    "central": "Samfya Central",
    "samfya": "Samfya Central",
    "chifunabuli": "Chifunabuli",
    "kasaba": "Kasaba",
    "lubwe": "Lubwe",
    "mabumba": "Mabumba",
    "mansa": "Mansa",
    "senama": "Senama",
    "chishi": "Chishi",
}


def standardise_ward(value: str) -> str:
    key = norm_ws(value).lower()
    if not key:
        return ""
    return WARD_MAP.get(key, norm_ws(value).title())


def standardise_council(value: str) -> str:
    v = norm_ws(value)
    if not v:
        return "Samfya Town Council"
    if "samfya" in v.lower():
        return "Samfya Town Council"
    return v


# ---------------------------------------------------------------------------
# Numeric / date parsers
# ---------------------------------------------------------------------------
def parse_amount_zmw(value) -> float | None:
    """
    Return a float ZMW value, or None if not unambiguously numeric.
    Handles: '2800000', '2.8-million-kwacha', 'K2,800,000', '2.8 million'.
    """
    s = norm_ws(value).lower()
    if not s:
        return None

    # strip currency words
    s = re.sub(r"\b(zmw|zambian\s+kwacha|kwacha|k)\b", " ", s)
    s = s.replace(",", "")
    s = norm_ws(s)

    multiplier = 1.0
    if "billion" in s:
        multiplier = 1_000_000_000.0
        s = s.replace("billion", " ").strip()
    elif "million" in s:
        multiplier = 1_000_000.0
        s = s.replace("million", " ").strip()

    # optional trailing k/m (thousand / million)
    m = re.match(r"^(\d+(?:\.\d+)?)\s*([km])?$", s)
    if m:
        num = float(m.group(1))
        suffix = m.group(2)
        if suffix == "k":
            num *= 1_000.0
        elif suffix == "m":
            num *= 1_000_000.0
        return num * multiplier

    # last-ditch: whole string looks numeric once non-numerics stripped
    stripped = re.sub(r"[^\d\.\-]", "", s)
    if stripped in ("", "-", ".", "-."):
        return None
    try:
        return float(stripped) * multiplier
    except ValueError:
        return None


_YEAR_RE = re.compile(r"(19|20)\d{2}")


def parse_year(value) -> str:
    s = norm_ws(value)
    if not s:
        return ""
    m = _YEAR_RE.search(s)
    return m.group(0) if m else ""


def parse_date_iso(value) -> str:
    """Best-effort ISO date (YYYY-MM-DD). Accepts full ISO timestamps too."""
    s = norm_ws(value)
    if not s:
        return ""
    # Handle full ISO timestamps like 2026-09-11T15:58:03+00:00
    try:
        return pd.to_datetime(s, errors="raise", utc=True).strftime("%Y-%m-%d")
    except Exception:
        pass
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y",
                "%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return pd.to_datetime(s, format=fmt).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            continue
    return ""


def parse_timestamp_iso(value) -> str:
    """Preserve full timestamp (UTC) where available; fall back to date only."""
    s = norm_ws(value)
    if not s:
        return ""
    try:
        return pd.to_datetime(s, errors="raise", utc=True).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return parse_date_iso(s)


# ---------------------------------------------------------------------------
# Dataset-specific cleaning
# ---------------------------------------------------------------------------
def clean_cdf_projects(log: list) -> pd.DataFrame:
    """
    Merge cdf_projects_seed (detailed project rows) with cdf_activities_seed
    (aggregate activity rows). Both are valid evidence; we keep them in one
    table with a shared schema.
    """
    proj = read_raw("db-unza26-csc4792-samfya_cdf_projects_seed.csv")
    acts = read_raw("db-unza26-csc4792-samfya_cdf_activities_seed.csv")

    frames = []
    if not proj.empty:
        proj = clean_strings(proj)
        proj["record_kind"] = "project"
        frames.append(proj)
        log.append(f"CDF projects: loaded projects seed ({len(proj)} rows)")
    if not acts.empty:
        acts = clean_strings(acts)
        acts["record_kind"] = "activity"
        frames.append(acts)
        log.append(f"CDF projects: loaded activities seed ({len(acts)} rows)")

    if not frames:
        log.append("No CDF source files found - skipping.")
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True, sort=False)

    # Unified target columns (raw columns preserved alongside)
    df["council_clean"] = df.get("council", "").map(standardise_council)
    df["constituency_clean"] = df.get("constituency", "").map(
        lambda x: norm_ws(x) or "Bangweulu Constituency")
    df["ward_clean"] = df.get("ward_raw", "").map(standardise_ward)

    # Project name: projects seed has project_name_raw; activities has description_raw
    name = df.get("project_name_raw", pd.Series([""] * len(df))).fillna("")
    desc = df.get("description_raw", pd.Series([""] * len(df))).fillna("")
    df["project_name_clean"] = [norm_ws(a) or norm_ws(b) for a, b in zip(name, desc)]

    # Project type: activities seed has activity_type_raw; projects seed has extraction_note
    atype = df.get("activity_type_raw", pd.Series([""] * len(df))).fillna("")
    df["project_type_clean"] = [norm_ws(a).title() for a in atype]

    df["status_clean"] = df.get("status_raw", "").map(standardise_status)
    df["year_clean"] = df.get("year_raw", "").map(parse_year)

    raw_amt = df.get("amount_zmw_raw", pd.Series([""] * len(df))).fillna("")
    df["amount_zmw_raw_kept"] = raw_amt.map(norm_ws)
    df["amount_zmw"] = raw_amt.map(parse_amount_zmw)

    df["funding_source_clean"] = df.get("funding_source_raw", "").map(
        lambda x: norm_ws(x) or "Constituency Development Fund (CDF)")

    # Source fields
    src_title = df.get("source_title", pd.Series([""] * len(df))).fillna("")
    src_type = df.get("source_type", pd.Series([""] * len(df))).fillna("")
    df["source_title_clean"] = [norm_ws(a) or norm_ws(b) for a, b in zip(src_title, src_type)]
    df["source_url_clean"] = df.get("source_url", "").map(norm_ws)

    # Drop rows with no name AND no source URL
    before = len(df)
    keep = (df["project_name_clean"] != "") | (df["source_url_clean"] != "")
    df = df[keep].copy()
    log.append(f"CDF projects: dropped {before - len(df)} unusable row(s).")

    df = drop_exact_duplicates(df, "CDF projects", log)

    # Reorder: put clean columns first, raw evidence after
    preferred = [
        "record_kind",
        "council_clean", "constituency_clean", "ward_clean",
        "project_name_clean", "project_type_clean", "status_clean", "year_clean",
        "amount_zmw_raw_kept", "amount_zmw", "funding_source_clean",
        "source_title_clean", "source_url_clean",
    ]
    others = [c for c in df.columns if c not in preferred]
    df = df[preferred + others]
    df = add_index_column(df, prefix="CDF")
    return df


def clean_council_resources(log: list) -> pd.DataFrame:
    live = read_raw("db-unza26-csc4792-samfya_resource_index.csv")
    if live.empty:
        log.append("Council resources: no live file found.")
        return pd.DataFrame()

    df = clean_strings(live)
    log.append(f"Council resources: loaded {len(df)} rows.")

    df["council_clean"] = df.get("council", "").map(standardise_council)
    df["document_title_clean"] = df.get("document_title_raw", "").map(norm_ws)
    df["document_url_clean"] = df.get("document_url", "").map(norm_ws)
    df["file_type_clean"] = df.get("file_type", "").map(
        lambda x: norm_ws(x).lower())
    df["source_page_clean"] = df.get("source_page", "").map(norm_ws)
    df["year_clean"] = df.get("year_raw", "").map(parse_year)
    df["category_clean"] = df.get("category", "").map(
        lambda x: norm_ws(x).replace("_", " ").title())
    df["retrieved_at_utc_clean"] = df.get("retrieved_at_utc", "").map(parse_timestamp_iso)

    before = len(df)
    df = df[(df["document_url_clean"] != "") | (df["document_title_clean"] != "")].copy()
    log.append(f"Council resources: dropped {before - len(df)} unusable row(s).")

    df = drop_exact_duplicates(df, "Council resources", log)

    preferred = [
        "council_clean", "category_clean", "year_clean",
        "document_title_clean", "file_type_clean",
        "document_url_clean", "source_page_clean", "retrieved_at_utc_clean",
    ]
    others = [c for c in df.columns if c not in preferred]
    df = df[preferred + others]
    df = add_index_column(df, prefix="RES")
    return df


def clean_news(log: list) -> pd.DataFrame:
    live = read_raw("db-unza26-csc4792-samfya_news.csv")
    if live.empty:
        log.append("News: no live file found.")
        return pd.DataFrame()

    df = clean_strings(live)
    log.append(f"News: loaded {len(df)} rows.")

    df["council_clean"] = df.get("council", "").map(standardise_council)
    df["title_clean"] = df.get("title_raw", "").map(norm_ws)
    df["published_date_clean"] = df.get("published_date_raw", "").map(parse_date_iso)
    df["excerpt_clean"] = df.get("excerpt_raw", "").map(norm_ws)
    df["article_text_clean"] = df.get("article_text_raw", "").map(norm_ws)
    df["article_url_clean"] = df.get("article_url", "").map(norm_ws)
    df["source_listing_page_clean"] = df.get("source_listing_page", "").map(norm_ws)
    df["linked_document_urls_clean"] = df.get("linked_document_urls", "").map(norm_ws)
    df["retrieved_at_utc_clean"] = df.get("retrieved_at_utc", "").map(parse_timestamp_iso)

    # Extract any ZMW amounts mentioned in the text (kept separately, best-effort)
    def extract_first_amount(text: str):
        if not text:
            return None
        m = re.search(
            r"(\d+(?:[.,]\d+)?)\s*[-\s]*(million|billion)?\s*[-\s]*kwacha",
            text, flags=re.IGNORECASE)
        if not m:
            return None
        num = float(m.group(1).replace(",", ""))
        unit = (m.group(2) or "").lower()
        if unit == "million":
            num *= 1_000_000
        elif unit == "billion":
            num *= 1_000_000_000
        return num

    df["mentioned_amount_zmw"] = df["article_text_clean"].map(extract_first_amount)

    before = len(df)
    df = df[(df["title_clean"] != "") | (df["article_url_clean"] != "")].copy()
    log.append(f"News: dropped {before - len(df)} unusable row(s).")

    df = drop_exact_duplicates(df, "News", log)

    preferred = [
        "council_clean", "title_clean", "published_date_clean",
        "excerpt_clean", "article_text_clean",
        "mentioned_amount_zmw",
        "article_url_clean", "source_listing_page_clean",
        "linked_document_urls_clean", "retrieved_at_utc_clean",
    ]
    others = [c for c in df.columns if c not in preferred]
    df = df[preferred + others]
    df = add_index_column(df, prefix="NEWS")
    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    log: list[str] = ["=== Samfya Town Council cleaning run ==="]

    cdf = clean_cdf_projects(log)
    res = clean_council_resources(log)
    news = clean_news(log)

    outputs = {
        "db-unza26-csc4792-samfya_cdf_projects.csv": cdf,
        "db-unza26-csc4792-samfya_council_resources.csv": res,
        "db-unza26-csc4792-samfya_news.csv": news,
    }

    for filename, frame in outputs.items():
        if frame.empty:
            log.append(f"SKIP {filename}: no rows.")
            continue
        out_path = CLEAN / filename
        frame.to_csv(out_path, sep=SEP, index=False, encoding=ENCODING)
        log.append(f"WROTE {out_path.relative_to(ROOT)} "
                   f"({len(frame)} rows x {len(frame.columns)} cols)")

    log_path = CLEAN / "cleaning_log.txt"
    log_path.write_text("\n".join(log), encoding=ENCODING)
    print("\n".join(log))


if __name__ == "__main__":
    main()