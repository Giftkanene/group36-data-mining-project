"""Extract text and tables from downloaded Samfya PDF documents.

This is intentionally a raw extraction stage. Person B should clean and
standardise the resulting table files rather than treating them as final data.
"""
from pathlib import Path
import re
import pandas as pd
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
DOWNLOAD_DIR = ROOT / "data" / "downloads"
OUTPUT_DIR = ROOT / "data" / "extracted_tables"
RESOURCE_INDEX = ROOT / "data" / "raw" / "db-unza26-csc4792-samfya_resource_index.csv"


def safe_stem(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_")[:100]


def source_url_lookup() -> dict[str, str]:
    """Map downloaded file names to their discovered source URLs when available."""
    if not RESOURCE_INDEX.exists():
        return {}
    resources = pd.read_csv(RESOURCE_INDEX, sep="|", dtype=str).fillna("")
    if "document_url" not in resources.columns:
        return {}
    return {
        Path(url).name: url
        for url in resources["document_url"]
        if url and Path(url).suffix.lower() == ".pdf"
    }


def is_cdf_evidence(text: str) -> bool:
    lowered = text.lower()
    terms = ("cdf", "constituency development fund", "community project", "ward development")
    return any(term in lowered for term in terms)


def extract_pdf(pdf_path: Path, source_url: str = "") -> tuple[list[dict], list[dict], list[dict]]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    index_rows = []
    cdf_rows = []
    table_manifest_rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            index_rows.append({
                "source_file": pdf_path.name,
                "source_url": source_url,
                "page": page_number,
                "text_raw": re.sub(r"\s+", " ", text).strip(),
            })
            if is_cdf_evidence(text):
                cdf_rows.append({
                    "source_file": pdf_path.name,
                    "source_url": source_url,
                    "page": page_number,
                    "text_raw": re.sub(r"\s+", " ", text).strip(),
                })
            tables = page.extract_tables() or []
            for table_number, table in enumerate(tables, start=1):
                if not table:
                    continue
                width = max(len(row or []) for row in table)
                normalized = [(row or []) + [None] * (width - len(row or [])) for row in table]
                df = pd.DataFrame(normalized)
                out = OUTPUT_DIR / f"{safe_stem(pdf_path.stem)}_p{page_number:03d}_t{table_number:02d}.csv"
                df.to_csv(out, sep="|", index=False, header=False, encoding="utf-8-sig")
                table_manifest_rows.append({
                    "source_file": pdf_path.name,
                    "source_url": source_url,
                    "page": page_number,
                    "table_number": table_number,
                    "table_file": out.name,
                    "cdf_related": is_cdf_evidence(text),
                })
    return index_rows, cdf_rows, table_manifest_rows


def run():
    pdfs = sorted(DOWNLOAD_DIR.glob("*.pdf"))
    all_rows = []
    cdf_rows = []
    table_manifest_rows = []
    urls_by_filename = source_url_lookup()
    for pdf_path in pdfs:
        print(f"[pdf] {pdf_path.name}")
        try:
            index_rows, evidence_rows, manifest_rows = extract_pdf(
                pdf_path, urls_by_filename.get(pdf_path.name, "")
            )
            all_rows.extend(index_rows)
            cdf_rows.extend(evidence_rows)
            table_manifest_rows.extend(manifest_rows)
        except Exception as exc:
            print(f"  WARNING: could not extract {pdf_path.name}: {exc}")
    index = pd.DataFrame(all_rows, columns=["source_file", "source_url", "page", "text_raw"])
    index.to_csv(
        OUTPUT_DIR / "db-unza26-csc4792-samfya_pdf_text_index.csv",
        sep="|", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame(cdf_rows, columns=["source_file", "source_url", "page", "text_raw"]).to_csv(
        OUTPUT_DIR / "db-unza26-csc4792-samfya_cdf_evidence_index.csv",
        sep="|", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame(
        table_manifest_rows,
        columns=["source_file", "source_url", "page", "table_number", "table_file", "cdf_related"],
    ).to_csv(
        OUTPUT_DIR / "db-unza26-csc4792-samfya_pdf_table_manifest.csv",
        sep="|", index=False, encoding="utf-8-sig"
    )
    print(
        f"PDF extraction complete: {len(pdfs)} PDFs, {len(index)} pages indexed, "
        f"{len(cdf_rows)} CDF evidence pages flagged."
    )


if __name__ == "__main__":
    run()
