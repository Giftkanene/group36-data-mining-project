# Person B Instructions - Data Cleaner

## Your responsibility

Person B must turn Person A's raw Samfya Town Council records into consistent, well-documented, pipe-separated CSV datasets. Do not overwrite or silently alter the raw source files. Add reproducible cleaning code, cleaned outputs, cleaning documentation, and a precise handoff for Person C.

Repository: <https://github.com/Giftkanene/group36-data-mining-project>

## 1. Clone the repository

Open PowerShell in the folder where you want to keep the project and run:

```powershell
git clone https://github.com/Giftkanene/group36-data-mining-project.git
cd group36-data-mining-project
git switch -c person-b-data-cleaning
```

The separate branch keeps Person B's work isolated until it has been checked and merged.

Before starting, confirm that the repository contains the latest Person A data:

```powershell
git log --oneline -5
git status
```

The history should include the commit `data: add validated live Samfya scrape`.

## 2. Understand the input files

All raw files are in `data/raw/` and use the pipe character `|` as the delimiter.

Use these live files first:

- `db-unza26-csc4792-samfya_resource_index.csv` - 90 discovered documents and council resources.
- `db-unza26-csc4792-samfya_news.csv` - 21 council news records, including full article text where the source supplied it.
- `db-unza26-csc4792-samfya_scrape_run_metadata.csv` - scrape date, source pages, and row counts.
- `db-unza26-csc4792-samfya_raw_validation_report.csv` - Person A's validation results.

Use these seed files as supporting raw evidence where relevant:

- `db-unza26-csc4792-samfya_cdf_projects_seed.csv`
- `db-unza26-csc4792-samfya_cdf_activities_seed.csv`
- `db-unza26-csc4792-samfya_resource_index_seed.csv`
- `db-unza26-csc4792-samfya_news_seed.csv`

The live files currently pass validation. Some seed records have incomplete direct URLs, so retain them only when another source field provides adequate provenance and document the limitation.

## 3. Set up the cleaning environment

Use the existing project environment or create one:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install pandas
```

If PowerShell blocks activation, the interpreter can be used directly:

```powershell
.\.venv\Scripts\python.exe -m pip install pandas
```

Add the cleaning dependencies you actually use to a new file named `requirements-cleaning.txt`. Do not commit `.venv/`.

## 4. Files Person B must add

Add all of the following to the repository:

1. `scripts/clean_data.py` - repeatable cleaning and preprocessing code.
2. `requirements-cleaning.txt` - packages required by the cleaning script.
3. `data/cleaned/` - final cleaned CSV files.
4. `CLEANING_NOTES.md` - every cleaning rule, assumption, and limitation.
5. A cleaning/preprocessing section in `notebooks/Group36_Dataming_Project.ipynb` with explanatory Markdown cells and runnable code.
6. `HANDOFF_TO_PERSON_C.md` - exact Kaggle-upload instructions for Person C.

Do not edit the raw CSVs in place. Read from `data/raw/` and write new files to `data/cleaned/`.

## 5. Required cleaning work

The cleaning script should perform and document these operations:

1. Read every CSV with `sep="|"` and string-safe settings.
2. Trim leading/trailing whitespace and normalise repeated internal whitespace.
3. Standardise council and ward names without discarding the original raw values when uncertainty exists.
4. Standardise project status values, for example `Completed`, `In progress`, `Under procurement`, `Deferred`, or `Proposed`.
5. Convert unambiguous monetary values to numeric ZMW fields. Keep the original amount text in a separate raw column.
6. Convert unambiguous dates and years to consistent formats.
7. Remove exact duplicates and review likely duplicates using source URL, title, ward, project name, and year.
8. Preserve `source_url`, `document_url`, `article_url`, `source_page`, and retrieval timestamps for traceability.
9. Keep genuinely missing values blank or `NA`; never invent data.
10. Record every rule and manual decision in `CLEANING_NOTES.md`.

Records reported in several sources are not automatically duplicates. For example, a council minute and a later news story may describe the same project at different stages. Retain separate records when they provide different dates, statuses, amounts, or evidence.

## 6. Recommended cleaned datasets

Use the required filename prefix and create the datasets supported by the available evidence:

- `data/cleaned/db-unza26-csc4792-samfya_cdf_projects.csv`
- `data/cleaned/db-unza26-csc4792-samfya_council_resources.csv`
- `data/cleaned/db-unza26-csc4792-samfya_news.csv`

Every final file must:

- Be a real CSV file.
- Use `|` as the separator.
- Use UTF-8 encoding.
- Follow the exact `db-unza26-csc4792-[DESCRIPTION].csv` naming convention.
- Have one header row and no unnamed index column.
- Preserve a usable provenance URL for each record whenever the source provides one.

A recommended CDF project schema is:

```text
council|constituency|ward|project_name|project_type|status|year|amount_zmw_raw|amount_zmw|funding_source|source_title|source_url
```

Person B may add useful columns, but each one must be explained in the Person C handoff.

## 7. Validate the cleaned outputs

Before committing, check:

- Each cleaned CSV has at least one data row.
- The delimiter is `|`, not a comma.
- Required columns are present.
- There are no accidental index columns such as `Unnamed: 0`.
- Numeric amount columns contain numbers or missing values only.
- Dates/years use consistent formats.
- Duplicate rules were applied and documented.
- Source URLs were preserved.
- The cleaning script can regenerate the outputs from `data/raw/`.
- The main notebook opens as valid `.ipynb` JSON and explains the cleaning process in Markdown.

Run the complete cleaning process again from a clean starting point before submission. Record final row counts in `CLEANING_NOTES.md` and `HANDOFF_TO_PERSON_C.md`.

## 8. Write exact instructions for Person C

Person B must create `HANDOFF_TO_PERSON_C.md`. It should contain these sections:

### Ready-to-upload files

For every cleaned file, state:

- Exact relative path and filename.
- Number of rows and columns.
- What one row represents.
- Which raw files were used.

### Kaggle dataset configuration

Tell Person C:

- The proposed dataset title: `Samfya Town Council Development and Council Records`.
- That every CSV uses the pipe (`|`) separator and UTF-8 encoding.
- Which cleaned files must be uploaded.
- That raw, seed, validation, virtual-environment, and temporary files must not be uploaded as the final Kaggle dataset.
- Which licence the group has agreed to use. If no licence has been agreed, explicitly tell Person C to confirm this with the group instead of guessing.

### Dataset description

Provide Person C with ready-to-use notes covering:

- Samfya Town Council and Bangweulu Constituency.
- Dataset purpose and coverage.
- Official council source pages.
- Collection date.
- Cleaning and deduplication methodology.
- File-by-file descriptions.
- Column definitions and units, especially ZMW amounts.
- Missing-value meaning.
- Known limitations and incomplete provenance.
- Suggested reuse cases.
- A link to this GitHub repository for reproducibility.

### Final Kaggle checks

Tell Person C to verify:

- Kaggle previews the files correctly with `|` as the separator.
- Row and column counts match Person B's handoff.
- The dataset description explains every file and important column.
- Source attribution and the GitHub link are included.
- No private information, credentials, local paths, `.venv` files, or temporary files are uploaded.

## 9. Commit and push the work to GitHub

Review the exact files before staging:

```powershell
git status
git diff
```

Add only Person B's intended deliverables:

```powershell
git add scripts/clean_data.py requirements-cleaning.txt data/cleaned CLEANING_NOTES.md HANDOFF_TO_PERSON_C.md notebooks/Group36_Dataming_Project.ipynb
git commit -m "data: add cleaned Samfya council datasets"
git pull --rebase origin main
git push -u origin person-b-data-cleaning
```

On GitHub, open a pull request from `person-b-data-cleaning` into `main`. Use a clear title such as:

```text
data: add cleaned Samfya council datasets
```

The pull-request description should state the cleaned filenames, final row counts, validation result, and known limitations. After the group reviews and merges it, Person C should pull or clone the updated `main` branch.

If Person B has explicit permission to work directly on `main`, they may instead run `git switch main`, `git pull`, commit, and `git push origin main`. A reviewed branch and pull request is safer for group work.

## 10. Person B completion checklist

- [ ] Repository cloned and a Person B branch created.
- [ ] Raw files left unchanged.
- [ ] Reproducible cleaning script added.
- [ ] Cleaning dependencies documented.
- [ ] Cleaned pipe-separated CSVs added under `data/cleaned/`.
- [ ] Required filename convention followed.
- [ ] Source URLs preserved.
- [ ] Duplicate, date, amount, and missing-value rules documented.
- [ ] Main notebook updated with cleaning and preprocessing steps.
- [ ] `CLEANING_NOTES.md` includes final row counts and limitations.
- [ ] `HANDOFF_TO_PERSON_C.md` gives exact Kaggle instructions.
- [ ] Changes committed with a descriptive message.
- [ ] Branch pushed to GitHub and pull request opened.
