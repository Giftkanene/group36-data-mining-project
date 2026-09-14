# Cleaning Notes — Samfya Town Council (Group 36)

## Reproduce

From the project root in an active virtual environment:

    python scripts\clean_data.py

If the environment doesn't exist yet:

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements-cleaning.txt

On Windows, if PowerShell blocks activation:

    Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

Or invoke Python directly without activating:

    .\.venv\Scripts\python.exe scripts\clean_data.py

## Inputs (unchanged)

All raw files live in `data/raw/` and are pipe-delimited, UTF-8. They are
**never modified in place** by the cleaning script.

Live files from the Group 36 scraping workflow:
- `db-unza26-csc4792-samfya_resource_index.csv` (90 rows)
- `db-unza26-csc4792-samfya_news.csv` (21 rows)
- `db-unza26-csc4792-samfya_scrape_run_metadata.csv`
- `db-unza26-csc4792-samfya_raw_validation_report.csv`

Seed files used as supporting evidence:
- `db-unza26-csc4792-samfya_cdf_projects_seed.csv` (22 rows)
- `db-unza26-csc4792-samfya_cdf_activities_seed.csv` (6 rows)
- `db-unza26-csc4792-samfya_resource_index_seed.csv`
- `db-unza26-csc4792-samfya_news_seed.csv`

## Outputs

| File | Rows | Cols |
|---|---|---|
| `data/cleaned/db-unza26-csc4792-samfya_cdf_projects.csv` | 28 | 30 |
| `data/cleaned/db-unza26-csc4792-samfya_council_resources.csv` | 90 | 17 |
| `data/cleaned/db-unza26-csc4792-samfya_news.csv` | 21 | 20 |

All outputs are UTF-8, pipe (`|`) separated, with a single header row and no
pandas index column.

## Cleaning rules applied

1. Every CSV read with `sep="|"`, `dtype=str`, `keep_default_na=False`,
   UTF-8. This preserves leading zeros, decimal-looking strings, and literal
   empty values without pandas coercing them.
2. Leading/trailing whitespace trimmed and repeated internal whitespace
   collapsed. Non-breaking spaces (`\u00a0`) normalised to regular spaces.
3. Council names standardised to `Samfya Town Council` via
   `standardise_council()`. The original `council` column is kept on the
   right-hand side of each output for traceability.
4. Ward names mapped via a curated `WARD_MAP` (`kapilibila` → `Kapilibila`,
   etc.). Unmapped wards are title-cased and left unchanged rather than
   discarded.
5. Project statuses standardised to one of: `Completed`, `In progress`,
   `Under procurement`, `Deferred`, `Proposed`, `Unknown`. The `Unknown`
   bucket captures empty values and unrecognised phrases.
6. Monetary values parsed to numeric `amount_zmw` (float, ZMW). Handles
   plain digits, comma-grouped numbers, `K`/`k` (thousand), `M`/`m`
   (million), and the words `million`/`billion`. The original text is
   preserved in the `amount_zmw_raw_kept` column.
7. Years extracted via regex `(19|20)\d{2}` from any free-text `year_raw`
   field; stored as a 4-character string or blank.
8. Dates normalised to ISO `YYYY-MM-DD`. Full ISO timestamps (e.g.
   `2026-09-11T15:58:03+00:00`) are normalised to
   `YYYY-MM-DDTHH:MM:SSZ` in `retrieved_at_utc_clean`.
9. Exact duplicate rows removed per dataset (none found in this run).
10. Rows with no identifying name **and** no source URL were dropped as
    unusable (none found in this run).
11. `source_url`, `document_url`, `article_url`, `source_page`,
    `source_listing_page`, and `retrieved_at_utc` preserved verbatim in the
    cleaned outputs.
12. Missing values left as empty strings — nothing is invented or imputed.
13. A stable `record_id` (`CDF0001`, `RES0001`, `NEWS0001`, ...) added as
    the first column of every output.

## Special handling: CDF projects + activities

The CDF evidence comes in two different shapes:

- **projects seed** (22 rows): one row per named project, with
  `project_name_raw`, `status_raw`, `ward_raw`, `source_title`, `source_url`.
- **activities seed** (6 rows): one row per funding/activity event, with
  `activity_type_raw`, `description_raw`, `quantity_raw`, `source_type`.

Both are valid evidence, so they are merged into one CDF table with a
`record_kind` column (`project` or `activity`). Dataset users can filter on this
column if they want a projects-only or activities-only view. Unification
columns:

- `project_name_clean` = `project_name_raw` for projects, `description_raw`
  for activities.
- `project_type_clean` = `activity_type_raw` (title-cased) for activities,
  blank for projects.
- `source_title_clean` = `source_title` for projects, `source_type` for
  activities.
- `funding_source_clean` = `funding_source_raw` or defaults to
  `Constituency Development Fund (CDF)`.
- `constituency_clean` = `constituency` or defaults to `Bangweulu
  Constituency`.

All original raw columns are preserved on the right side of the output.

## News amounts

The news file mentions monetary values in prose (e.g.
*"2.8-million-kwacha Constituency Development Fund"*). A best-effort regex
extracts the first such figure into the `mentioned_amount_zmw` column. This
column is **informational only** — it is not a substitute for the CDF
project amounts and should not be summed with `amount_zmw` from the CDF
table.

## Assumptions and manual decisions

- Empty `status_clean` → `Unknown`; the raw source did not state a status.
- Empty `amount_zmw` → the raw text was not unambiguously numeric
  (`amount_zmw_raw_kept` still shows what the source said).
- Empty `year_clean` → no 4-digit year could be extracted from the source.
- The `serial_number_raw` field in the projects seed is preserved but not
  used as a key, because it restarts per minute-book.
- Where the source had a `ward_raw` value not present in `WARD_MAP`, the
  cleaned value is a title-cased copy of the raw value. This is deliberate —
  silently discarding unknown wards would hide data.

## Known limitations

- Some seed records do not carry a direct URL for the underlying document.
  Provenance is therefore weaker for those rows. They were retained only
  where a source title or description is present.
- The status vocabulary in the raw data is ad hoc. The map is curated but
  unusual phrasings will land in `Unknown`.
- Amount parsing cannot distinguish between a budgeted figure and a
  disbursed/actual figure if the source text did not say which it was.
- The news `mentioned_amount_zmw` is the first amount the regex finds in an
  article, not necessarily the article's headline figure.
- Ward names outside the built-in `WARD_MAP` remain as free text.

## Final validation

- [x] Every cleaned CSV has ≥ 1 data row.
- [x] Delimiter is `|`, not `,`.
- [x] Encoding is UTF-8.
- [x] No `Unnamed: 0` index columns.
- [x] `amount_zmw` contains numbers or blanks only.
- [x] `year_clean` is 4-digit or blank.
- [x] Dates use ISO format.
- [x] Source URLs preserved.
- [x] Script is re-runnable from `data/raw/` and produces identical output.
- [x] Raw files untouched.
