import hashlib
import os
import time
import re
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
# STRICT BID / REGULATION VALIDATION (CORE LOGIC)
# ======================================================

def is_valid_bid_update(text: str, href: str) -> bool:
    text = (text or "").strip().lower()
    href = (href or "").lower()

    # ---- 1. Reject empty / very short ----
    if len(text) < 15:
        return False

    # ---- 2. Reject numeric counters ----
    if re.fullmatch(r"\d+", text):
        return False

    # ---- 3. Reject UI / navigation noise ----
    UI_NOISE = [
        "active tenders", "bids", "search", "calendar",
        "closing today", "recent tenders", "dashboard",
        "statistics", "total", "count",
        "home", "welcome", "login", "register",
        "faq", "help", "support",
        "model tender documents", "tender calendar",
        "web information manager", "skip to",
        "screen reader", "accessibility",
        "policies", "training", "courses",
        "ask", "chat", "contact", "about"
    ]

    if any(n in text for n in UI_NOISE):
        return False

    # ---- 4. Strong regulatory / document signals ----
    STRONG_SIGNALS = [
        "corrigendum", "amendment", "addendum",
        "notification", "circular",
        "rule", "gfr", "guideline", "manual",
        "eligibility", "qualification",
        "suspended", "debarred", "blacklisted",
        "extension", "deadline",
        "tender no", "bid no", "reference",
        "document", "clause"
    ]

    if any(s in text for s in STRONG_SIGNALS):
        return True

    # ---- 5. URL-based confirmation (PDF / notice pages) ----
    if any(s in href for s in ["corrigendum", "amendment", "circular", "notification", "pdf"]):
        return True

    return False

# ======================================================
# TAGGING
# ======================================================

def tag_update(text: str) -> str:
    text = text.lower()

    if any(x in text for x in ["corrigendum", "amendment", "addendum"]):
        return "AMENDMENT"
    if any(x in text for x in ["deadline", "extension"]):
        return "DEADLINE_CHANGE"
    if "eligibility" in text:
        return "ELIGIBILITY_UPDATE"
    if any(x in text for x in ["rule", "gfr", "guideline", "manual"]):
        return "REGULATION_UPDATE"
    if any(x in text for x in ["suspended", "debarred", "blacklisted"]):
        return "COMPLIANCE_ACTION"

    return "BID_DOCUMENT"

def hash_content(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

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
# SCRAPERS (STRICT)
# ======================================================

def scrape_gem():
    print("\n🌐 Scraping GeM (safe session handling)")
    url = "https://gem.gov.in/search/search_tender"
    driver = setup_driver()
    entries = []

    try:
        driver.get(url)
        time.sleep(6)

        elements = driver.find_elements(By.XPATH, "//a[@href]")

        for elem in elements:
            try:
                title = elem.text.strip()
                href = elem.get_attribute("href")

                if not title or len(title) < 15:
                    continue

                if not is_valid_bid_update(title, href):
                    continue

                entries.append({
                    "title": title,
                    "summary": f"GeM Regulatory / Bid Update: {title}",
                    "link": href,
                    "source": "GeM Portal",
                    "published": datetime.utcnow().isoformat()
                })

            except Exception:
                continue

    finally:
        driver.quit()

    print(f"✓ GeM accepted records: {len(entries)}")
    return entries


def scrape_cppp():
    print("\n🌐 Scraping CPP Portal (safe session handling)")
    url = "https://eprocure.gov.in/cppp/"
    driver = setup_driver()
    entries = []

    try:
        driver.get(url)
        time.sleep(6)

        elements = driver.find_elements(By.XPATH, "//a[@href]")

        for elem in elements:
            try:
                title = elem.text.strip()
                href = elem.get_attribute("href")

                if not title or len(title) < 15:
                    continue

                # STRICT filtering (same as before)
                if not is_valid_bid_update(title, href):
                    continue

                # IMPORTANT: store raw strings, not WebElements
                entries.append({
                    "title": title,
                    "summary": f"CPPP Regulatory / Bid Update: {title}",
                    "link": href,
                    "source": "CPP Portal",
                    "published": datetime.utcnow().isoformat()
                })

            except Exception:
                continue

    finally:
        # 🔴 driver.quit ONLY after all data is extracted
        driver.quit()

    print(f"✓ CPPP accepted records: {len(entries)}")
    return entries

def scrape_maharashtra_etender():
    url = "https://mahatenders.gov.in"
    driver = setup_driver()
    entries = []

    try:
        driver.get(url)
        time.sleep(6)

        links = driver.find_elements(By.XPATH, "//a[@href]")

        for elem in links:
            title = elem.text.strip()
            href = elem.get_attribute("href")

            if not is_valid_bid_update(title, href):
                continue

            entries.append({
                "title": title,
                "summary": f"Maharashtra eTender Update: {title}",
                "link": href,
                "source": "Maharashtra eTender",
                "published": datetime.utcnow().isoformat()
            })

    finally:
        driver.quit()

    return entries

# ======================================================
# MAIN PIPELINE
# ======================================================

def run_backend():
    print("\n" + "=" * 80)
    print("🚀 TenderFlow – BID DOCUMENTATION & REGULATION INGESTION")
    print("=" * 80)

    all_entries = []
    all_entries.extend(scrape_gem())
    all_entries.extend(scrape_cppp())
    all_entries.extend(scrape_maharashtra_etender())

    print(f"\n📊 TOTAL VALID RECORDS FOUND: {len(all_entries)}")

    inserted = 0

    for entry in all_entries:
        combined = f"{entry['title']} {entry['summary']}"

        payload = {
            "title": entry["title"][:500],
            "summary": entry["summary"][:2000],
            "link": entry["link"],
            "source": entry["source"],
            "published_at": entry["published"],
            "content_hash": hash_content(combined),
            "tag": tag_update(combined),
            "fetched_at": datetime.utcnow().isoformat(),
        }

        supabase.table("regulation_updates") \
            .upsert(payload, on_conflict="content_hash") \
            .execute()

        inserted += 1
        print("➕ Inserted:", entry["title"][:90])

    print("\n" + "=" * 80)
    print("✅ INGESTION COMPLETE")
    print(f"   INSERTED RECORDS: {inserted}")
    print("=" * 80 + "\n")

# ======================================================
# ENTRY POINT
# ======================================================

if __name__ == "__main__":
    run_backend()
