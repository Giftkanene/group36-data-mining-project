# Handoff — Person B → Person C (Kaggle upload)

**From:** Person B (data cleaning)
**To:** Person C (Kaggle publishing)
**Repo:** https://github.com/Giftkanene/group36-data-mining-project
**Branch to pull from:** `person-b-data-cleaning` (or `main` once merged)

---

## Ready-to-upload files

Three cleaned CSVs live in `data/cleaned/`. All are UTF-8, pipe (`|`)
separated, single header row, no index column.

### 1. `data/cleaned/db-unza26-csc4792-samfya_cdf_projects.csv`

- **Rows / Cols:** 28 / 30
- **One row =** one reported Constituency Development Fund (CDF) project or
  funding activity in Bangweulu Constituency, Samfya District.
- **Raw sources:** `db-unza26-csc4792-samfya_cdf_projects_seed.csv`
  (22 rows), `db-unza26-csc4792-samfya_cdf_activities_seed.csv` (6 rows).
- **`record_kind` column distinguishes:**
  - `project` — a named, specific project with a status.
  - `activity` — an aggregate funding event (e.g. group empowerment grants).
- **Key columns:**
  - `record_id` — stable ID (`CDF0001`...).
  - `council_clean`, `constituency_clean`, `ward_clean`.
  - `project_name_clean` — title of the project/activity.
  - `project_type_clean` — for activities, e.g. "Empowerment Grants".
  - `status_clean` — `Completed` / `In progress` / `Under procurement` /
    `Deferred` / `Proposed` / `Unknown`.
  - `year_clean` — 4-digit year or blank.
  - `amount_zmw_raw_kept` — the original amount text from the source.
  - `amount_zmw` — numeric ZMW value (float). **Blank means unknown, not
    zero.**
  - `funding_source_clean` — usually `Constituency Development Fund (CDF)`.
  - `source_title_clean`, `source_url_clean` — provenance.
  - All original raw columns are preserved on the right.

### 2. `data/cleaned/db-unza26-csc4792-samfya_council_resources.csv`

- **Rows / Cols:** 90 / 17
- **One row =** one document or resource listed on the Samfya Town Council
  website (PDFs, minute books, proposed project lists, etc.).
- **Raw source:** `db-unza26-csc4792-samfya_resource_index.csv`.
- **Key columns:**
  - `record_id` (`RES0001`...).
  - `council_clean`, `category_clean`, `year_clean`.
  - `document_title_clean`, `file_type_clean` (pdf, docx, ...).
  - `document_url_clean` — direct link to the file.
  - `source_page_clean` — the council web page the link was found on.
  - `retrieved_at_utc_clean` — ISO 8601 UTC timestamp of the scrape.

### 3. `data/cleaned/db-unza26-csc4792-samfya_news.csv`

- **Rows / Cols:** 21 / 20
- **One row =** one council news article.
- **Raw source:** `db-unza26-csc4792-samfya_news.csv`.
- **Key columns:**
  - `record_id` (`NEWS0001`...).
  - `council_clean`, `title_clean`, `published_date_clean` (ISO date).
  - `excerpt_clean`, `article_text_clean` (full body where the source
    supplied it).
  - `mentioned_amount_zmw` — best-effort first ZMW amount mentioned in the
    text. **Informational only; do not sum with the CDF amounts.**
  - `article_url_clean`, `source_listing_page_clean`,
    `linked_document_urls_clean`, `retrieved_at_utc_clean`.

---

## Kaggle dataset configuration

- **Proposed dataset title:** `Samfya Town Council Development and Council
  Records`
- **Proposed URL slug (if Kaggle asks):**
  `samfya-town-council-development-and-council-records`
- **Separator for every file:** pipe `|`
- **Encoding:** UTF-8
- **Upload exactly these three files** (no others):
  1. `db-unza26-csc4792-samfya_cdf_projects.csv`
  2. `db-unza26-csc4792-samfya_council_resources.csv`
  3. `db-unza26-csc4792-samfya_news.csv`
- **Do NOT upload:**
  - Anything from `data/raw/` (raw scrape, seed files, validation report,
    metadata).
  - The `.venv/` folder or anything inside it.
  - `cleaning_log.txt`, temporary files, cache folders, `.ipynb_checkpoints`.
  - Local paths, credentials, or anything not meant for public release.
- **Licence:** **Not yet confirmed by the group.** Ask the group which
  licence to publish under (CC BY 4.0 and CC0 are common for open data) and
  set it in the Kaggle dataset settings. Do not guess.

---

## Dataset description (ready to paste into Kaggle)

> **Samfya Town Council Development and Council Records**
>
> This dataset covers Samfya Town Council and Bangweulu Constituency in
> Luapula Province, Zambia. It combines three cleaned tables:
>
> 1. **CDF projects and activities** — Constituency Development Fund
>    projects, procurement status, funding source, and ZMW amounts reported
>    in council minutes and council news.
> 2. **Council resources** — an index of documents and files published on
>    the Samfya Town Council website (project lists, minute books, reports).
> 3. **Council news** — articles published on the council website,
>    including full text where available.
>
> All files use the pipe (`|`) separator and UTF-8 encoding. Data was
> collected from official Samfya Town Council source pages in September
> 2026.
>
> **Cleaning.** Whitespace was normalised; council and ward names were
> standardised; project statuses were mapped to a controlled vocabulary
> (`Completed`, `In progress`, `Under procurement`, `Deferred`, `Proposed`,
> `Unknown`); monetary values were parsed to numeric ZMW with the original
> text preserved in a parallel `*_raw_kept` column; dates were normalised to
> ISO 8601; exact duplicate rows were removed. Likely duplicates that
> appear across sources (e.g. a minute and a later news story covering the
> same project at different stages) were retained when they provide
> different dates, statuses, or amounts.
>
> **Missing values.** Empty cells indicate that the source did not provide
> the information. No value was imputed or invented.
>
> **Units.** `amount_zmw` is in Zambian Kwacha (ZMW). `mentioned_amount_zmw`
> in the news file is a best-effort extraction from article prose and should
> not be summed with the CDF amounts.
>
> **Provenance.** Every record preserves a source URL (`source_url_clean`,
> `document_url_clean`, `article_url_clean`) and a retrieval timestamp
> (`retrieved_at_utc_clean`) so results can be traced back to the original
> page.
>
> **Known limitations.** Some seed records carry no direct document URL, so
> provenance is weaker for those rows. Status vocabulary in the raw data is
> ad hoc, so unusual phrasings land in `Unknown`. Ward names outside the
> built-in map remain as free text. Amount parsing cannot distinguish
> budgeted from disbursed figures if the source did not say.
>
> **Suggested reuse.** Ward-level development monitoring; CDF budget and
> disbursement analysis; council transparency and open-data dashboards;
> NLP on council news and minute books; time-series analysis of project
> status transitions.
>
> **Reproducibility.** Cleaning code, raw data, and full documentation:
> https://github.com/Giftkanene/group36-data-mining-project

---

## Final checks before you click Publish

- [ ] Kaggle previews every file with `|` as the separator (check the
      "Preview" tab — if the columns look mashed together, the separator
      wasn't detected; re-upload and confirm the delimiter).
- [ ] Row and column counts on Kaggle match this handoff:
  - CDF projects: **28 rows × 30 cols**
  - Council resources: **90 rows × 17 cols**
  - News: **21 rows × 20 cols**
- [ ] Dataset description above is pasted in and mentions each file.
- [ ] Column definitions are covered in the description (especially
  `amount_zmw` units and `record_kind`).
- [ ] Source attribution (Samfya Town Council, official site) is present.
- [ ] GitHub link is present.
- [ ] Licence is set — **confirm with the group first.**
- [ ] No private info, credentials, local paths, `.venv` files, or
      temporary files are included.

---

## Questions or issues

If a file fails to upload or previews incorrectly, message Person B before
changing anything. Do not edit the cleaned CSVs directly — the whole point
is that they can be regenerated from `scripts/clean_data.py`.