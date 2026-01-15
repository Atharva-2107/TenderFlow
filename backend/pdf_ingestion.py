import os
import re
import time
import hashlib
import requests
import pdfplumber
from io import BytesIO
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ======================================================
# ENV SETUP
# ======================================================

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError("Supabase credentials missing")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ======================================================
# SELENIUM SETUP
# ======================================================

def setup_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    )
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

# ======================================================
# DEEP NAVIGATION — DETAIL PAGE DISCOVERY
# ======================================================

def discover_detail_pages(driver, seed_url: str, limit: int = 10) -> list[str]:
    """
    Discover tender / detail pages from a seed page.
    """
    detail_links = set()

    driver.get(seed_url)
    time.sleep(6)

    anchors = driver.find_elements(By.XPATH, "//a[@href]")

    for a in anchors:
        href = a.get_attribute("href")
        text = (a.text or "").lower()

        if not href:
            continue

        if (
            any(k in href.lower() for k in [
                "tender", "bid", "detail", "view", "corrigendum"
            ]) or
            any(k in text for k in [
                "view", "details", "corrigendum", "tender"
            ])
        ):
            detail_links.add(href)

        if len(detail_links) >= limit:
            break

    return list(detail_links)

# ======================================================
# DEEP NAVIGATION — PDF DISCOVERY
# ======================================================

def deep_pdf_discovery(seed_url: str, limit: int = 10) -> list[str]:
    """
    Seed page → Detail pages → PDFs
    """
    driver = setup_driver()
    pdf_links = set()

    try:
        print(f"\n🌐 Seed page: {seed_url}")

        detail_pages = discover_detail_pages(driver, seed_url, limit=limit)
        print(f"   🔍 Detail pages found: {len(detail_pages)}")

        for page_url in detail_pages:
            driver.get(page_url)
            time.sleep(5)

            anchors = driver.find_elements(By.XPATH, "//a[@href]")
            for a in anchors:
                href = a.get_attribute("href")
                if href and ".pdf" in href.lower():
                    pdf_links.add(href)

    finally:
        driver.quit()

    print(f"   📄 PDFs found via deep navigation: {len(pdf_links)}")
    return list(pdf_links)

# ======================================================
# PDF DOWNLOAD — IN MEMORY
# ======================================================

def download_pdf_bytes(pdf_url: str) -> bytes | None:
    try:
        r = requests.get(pdf_url, timeout=30)
        r.raise_for_status()
        return r.content
    except Exception as e:
        print(f"   ❌ PDF download failed: {e}")
        return None

# ======================================================
# PDF TEXT EXTRACTION — IN MEMORY
# ======================================================

def extract_pdf_text_from_bytes(pdf_bytes: bytes) -> str:
    text = []
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
    except Exception:
        return ""

    return "\n".join(text)

# ======================================================
# BID DOCUMENT PARSING
# ======================================================

def parse_tender_data(text: str) -> dict:
    data = {}

    tender_match = re.search(
        r"(Tender|Bid)\s*(No\.?|Number)?\s*[:\-]?\s*([A-Z0-9\/\-]+)",
        text, re.IGNORECASE
    )
    if tender_match:
        data["tender_no"] = tender_match.group(3)

    deadline_match = re.search(
        r"(Last Date|Closing Date|Bid Submission).*?(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})",
        text, re.IGNORECASE
    )
    if deadline_match:
        data["submission_deadline"] = deadline_match.group(2)

    emd_match = re.search(
        r"(EMD|Earnest Money).*?(₹|Rs\.?)\s?([\d,]+)",
        text, re.IGNORECASE
    )
    if emd_match:
        data["emd_amount"] = emd_match.group(3)

    eligibility = re.search(
        r"(Eligibility Criteria.*?)(?:\n\n|\Z)",
        text, re.IGNORECASE | re.DOTALL
    )
    if eligibility:
        data["eligibility_text"] = eligibility.group(1)[:1500]

    if re.search(r"corrigendum|amendment|addendum", text, re.IGNORECASE):
        data["document_type"] = "AMENDMENT"
    else:
        data["document_type"] = "TENDER_DOCUMENT"

    return data

def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

# ======================================================
# MAIN PIPELINE (PHASE 2–4 WITH DEEP NAVIGATION)
# ======================================================

def process_entry(source: str, source_url: str):
    print(f"\n🔍 Processing seed page: {source_url}")

    pdf_links = deep_pdf_discovery(source_url, limit=10)

    if not pdf_links:
        print("   ⚠️ No PDFs found after deep navigation")
        return

    for pdf_url in pdf_links:
        pdf_bytes = download_pdf_bytes(pdf_url)
        if not pdf_bytes:
            continue

        extracted_text = extract_pdf_text_from_bytes(pdf_bytes)
        if len(extracted_text) < 500:
            continue

        structured = parse_tender_data(extracted_text)
        content_hash = hash_text(extracted_text)

        payload = {
            "source": source,
            "source_url": source_url,
            "pdf_url": pdf_url,
            "tender_no": structured.get("tender_no"),
            "document_type": structured.get("document_type"),
            "extracted_text": extracted_text,
            "structured_data": structured,
            "content_hash": content_hash,
            "published_at": datetime.utcnow().isoformat(),
            "fetched_at": datetime.utcnow().isoformat(),
        }

        supabase.table("tender_documents") \
            .upsert(payload, on_conflict="content_hash") \
            .execute()

        print(f"   ✅ Inserted document: {structured.get('tender_no', 'UNKNOWN')}")

# ======================================================
# ENTRY POINT
# ======================================================

if __name__ == "__main__":
    rows = supabase.table("regulation_updates") \
        .select("source, link") \
        .execute()

    print(f"\n📥 Seed pages received: {len(rows.data)}")

    for row in rows.data:
        process_entry(row["source"], row["link"])
