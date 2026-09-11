# Handoff to Person B — Data Cleaner

## Files to start with

Start with the four pipe-separated files in `data/raw/` whose names end in `_seed.csv`.
When Person A runs the live scraper on an internet-connected computer, also use the generated non-seed files.

Before cleaning, open `db-unza26-csc4792-samfya_raw_validation_report.csv`. Do not use an empty live output as evidence; use the seed file instead and flag the live-site limitation in the methodology.

## Cleaning priorities

1. Remove exact duplicates by source URL + title or ward + project name + year.
2. Standardise ward names (capitalisation and spelling).
3. Standardise project status values such as `Under procurement`, `Completed`, `Ready for commissioning`.
4. Convert amount fields to numeric ZMW where the raw text provides a clear amount.
5. Standardise years/dates.
6. Keep the original `source_url`/`article_url` columns for traceability.
7. Do not silently invent missing values. Keep them blank/NA and document the cleaning rule.
8. Preserve raw values in separate columns if you transform them (for example `amount_zmw_raw` and `amount_zmw`).
9. Treat rows without a direct `document_url` or `article_url` as incomplete provenance. Keep them only when the `source_page`/`source_url` is retained and the limitation is noted.

## Recommended cleaned project schema

```text
council|constituency|ward|project_name|project_type|status|year|amount_zmw|funding_source|source_title|source_url
```

## High-value sources already identified

- CDF Community Projects page
- Grants and Loans page
- Skills and Bursaries page
- Publications page
- Council Minutes
- Budgets and Financial Statements
- Samfya IDP
- News posts reporting CDF and infrastructure activities

## Caution

Some records appear in more than one source (for example council minutes and later news stories). Treat them as candidate duplicates, not automatically as different projects.
