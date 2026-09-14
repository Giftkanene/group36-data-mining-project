# CSC 4792 Mini Project — Group 36
## Person A: Scraper Lead — Samfya Town Council

This folder is the handoff package for **Person A (Scraper Lead)** in **Project Group 36**.
The assigned local authority is **Samfya Town Council**.

Official council website: https://www.samfyacouncil.gov.zm

## What is included

- A reusable Python scraper for Samfya Town Council.
- Automatic discovery of council documents (CDF projects, grants/loans, bursaries, publications, budgets, minutes and financial statements).
- A news/article scraper with pagination.
- Full public article text and linked-document URLs for traceability.
- A document downloader for linked PDFs and all office documents.
- A PDF extraction helper using `pdfplumber`, including a CDF evidence index and table manifest.
- A validation script that checks row counts, required columns, pipe delimiters, duplicate URLs and missing provenance URLs.
- A Jupyter notebook showing the scraping workflow and methodology.
- Pipe-separated raw/seed CSV files so Person B can start cleaning immediately.
- A handoff note explaining what Person B should do next.

## Important assignment formatting rule

All CSV files produced by this package use the **pipe character `|` as the separator** and follow the naming pattern:

`db-unza26-csc4792-[DESCRIPTION].csv`

## Fastest way to run on Windows

1. Install Python 3.10+ from https://www.python.org/downloads/windows/ and tick **Add Python to PATH** during installation.
2. Open Command Prompt in this folder.
3. Run:

```bat
RUN_SCRAPER_WINDOWS.bat
```

The batch file creates a virtual environment, as well as installs requirements and runs the scraper.
It also replaces an incomplete/broken `.venv` automatically. The original project had a virtual environment pointing at an unavailable Windows Store Python installation; this improved package intentionally does not include that broken environment.

## Manual run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/run_all.py
python scripts/validate_raw_data.py
```

On macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/run_all.py
```

## Main outputs after a live run

The scraper writes the following files into `data/raw/`:

- `db-unza26-csc4792-samfya_resource_index.csv`
- `db-unza26-csc4792-samfya_news.csv`
- `db-unza26-csc4792-samfya_scrape_run_metadata.csv`

If document downloading is enabled, files are stored in `data/downloads/`.
The PDF extractor writes an index and table extracts to `data/extracted_tables/`.
It also writes `db-unza26-csc4792-samfya_cdf_evidence_index.csv` so CDF-relevant pages can be reviewed before values are normalised.

PDF extraction uses larger optional packages that are not needed for the live website scrape. Install them only when required:

```bash
pip install -r requirements-pdf.txt
python scripts/extract_pdf_tables.py
```

## Seed data already supplied

Seed raw files based on publicly indexed Samfya Town Council pages and documents are retained as a reproducible fallback and comparison set. The populated non-seed files are the latest live scraper outputs; Person B should use those first and consult the seed files only where their provenance is adequate.

Seed files:

- `db-unza26-csc4792-samfya_resource_index_seed.csv`
- `db-unza26-csc4792-samfya_news_seed.csv`
- `db-unza26-csc4792-samfya_cdf_projects_seed.csv`
- `db-unza26-csc4792-samfya_cdf_activities_seed.csv`

These are **raw handoff files**, not the final cleaned Kaggle dataset.

## Required pre-handoff check

After a live run, execute:

```bash
python scripts/validate_raw_data.py
```

Do not hand the live `resource_index.csv` or `news.csv` to Person B if the validation report shows an empty-output error. Resolve or document every missing direct evidence URL before final Kaggle preparation.

## Suggested GitHub commit messages

```text
feat: add Samfya Town Council document discovery scraper
feat: add paginated council news scraper
feat: add PDF downloader and extraction utilities
data: add initial Samfya raw scrape seed files
docs: document scraper methodology and handoff workflow
```

## Ethics / respectful scraping

The scraper uses a descriptive User-Agent, timeout handling, retries, deduplication and a delay between requests. Do not increase the request rate aggressively. The aim is academic data collection from public council pages, not load testing the server.

## Current Samfya website certificate issue

At the time this package was prepared, the official Samfya Town Council website presented an expired HTTPS certificate. The scraper verifies certificates normally first. If that specific verification fails for an official `samfyacouncil.gov.zm` page, it logs a warning and retries that public, non-authenticated page without certificate verification. This narrowly scoped fallback makes the public data accessible while keeping the limitation explicit in the terminal output and scrape metadata.


Last reviewed: 09/14/2026