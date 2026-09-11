from samfya_scraper import ScrapeConfig, run as run_scraper
from extract_pdf_tables import run as run_pdf_extractor

if __name__ == "__main__":
    # First pass: discover web resources and news. Keep downloads off by default
    # so the user can review the resource index before downloading many files.
    resources, news = run_scraper(
        ScrapeConfig(download_documents=False, fetch_article_details=True)
    )

    print("\nNEXT STEP (optional):")
    print("To download linked documents, edit download_documents=True in this file")
    print("or run the scraper from Python with ScrapeConfig(download_documents=True).")
    print("After PDFs are downloaded, run: python scripts/extract_pdf_tables.py")
