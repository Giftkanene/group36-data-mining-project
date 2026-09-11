"""Validate raw CSC 4792 scraper outputs before handing them to Person B.

The script does not alter source data. It writes a pipe-separated validation
report so that missing URLs, empty live runs and duplicated records are visible
before cleaning starts.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
REPORT_PATH = RAW_DIR / "db-unza26-csc4792-samfya_raw_validation_report.csv"

EXPECTED_COLUMNS = {
    "db-unza26-csc4792-samfya_resource_index_seed.csv": {
        "council", "category", "document_title_raw", "document_url", "source_page",
    },
    "db-unza26-csc4792-samfya_resource_index.csv": {
        "council", "category", "document_title_raw", "document_url", "source_page",
    },
    "db-unza26-csc4792-samfya_news.csv": {
        "council", "title_raw", "article_url", "source_listing_page",
    },
    "db-unza26-csc4792-samfya_news_seed.csv": {
        "council", "title_raw", "article_url", "source_listing_page",
    },
    "db-unza26-csc4792-samfya_cdf_projects_seed.csv": {
        "council", "ward_raw", "project_name_raw", "source_url",
    },
    "db-unza26-csc4792-samfya_cdf_activities_seed.csv": {
        "council", "activity_type_raw", "description_raw", "source_url",
    },
}


def read_pipe_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="|")
        return list(reader), reader.fieldnames or []


def add_issue(
    issues: list[dict[str, str]], file_name: str, severity: str, check: str, details: str
) -> None:
    issues.append({
        "file_name": file_name,
        "severity": severity,
        "check": check,
        "details": details,
    })


def validate_file(path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    rows, fieldnames = read_pipe_csv(path)
    expected = EXPECTED_COLUMNS.get(path.name, set())
    missing_columns = sorted(expected - set(fieldnames))
    if missing_columns:
        add_issue(issues, path.name, "error", "required_columns", f"Missing: {', '.join(missing_columns)}")
        return issues

    if not rows:
        severity = "error" if not path.name.endswith("_seed.csv") else "warning"
        add_issue(issues, path.name, severity, "row_count", "No data rows found")
        return issues

    url_column = next((name for name in ("document_url", "article_url", "source_url") if name in fieldnames), "")
    if url_column:
        missing_urls = sum(not (row.get(url_column) or "").strip() for row in rows)
        if missing_urls:
            add_issue(
                issues,
                path.name,
                "warning",
                "provenance_url",
                f"{missing_urls}/{len(rows)} rows have no {url_column}",
            )
        # One PDF can correctly evidence several CDF project rows. URL uniqueness
        # is therefore only a useful duplicate signal for document/news indexes.
        if "resource_index" in path.name or "news" in path.name:
            populated_urls = [row[url_column].strip() for row in rows if row.get(url_column, "").strip()]
            duplicates = [url for url, count in Counter(populated_urls).items() if count > 1]
            if duplicates:
                add_issue(
                    issues,
                    path.name,
                    "warning",
                    "duplicate_url",
                    f"{len(duplicates)} repeated {url_column} value(s)",
                )

    add_issue(issues, path.name, "pass", "row_count", f"{len(rows)} data row(s) read with pipe delimiter")
    return issues


def run() -> int:
    issues: list[dict[str, str]] = []
    for file_name in EXPECTED_COLUMNS:
        path = RAW_DIR / file_name
        if not path.exists():
            add_issue(issues, file_name, "error", "file_exists", "Expected file is missing")
            continue
        issues.extend(validate_file(path))

    with REPORT_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["file_name", "severity", "check", "details"], delimiter="|")
        writer.writeheader()
        writer.writerows(issues)

    errors = sum(issue["severity"] == "error" for issue in issues)
    warnings = sum(issue["severity"] == "warning" for issue in issues)
    print(f"Validation report: {REPORT_PATH}")
    print(f"Errors: {errors}; warnings: {warnings}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(run())
