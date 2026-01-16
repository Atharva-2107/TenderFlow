import hashlib
import os
import time
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
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
# VALIDATION LOGIC (UNCHANGED)
# ======================================================

def is_valid_bid_update(text: str, href: str) -> bool:
    text = (text or "").strip().lower()
    href = (href or "").lower()

    if len(text) < 15:
        return False

    if re.fullmatch(r"\d+", text):
        return False

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

    if any(s in href for s in ["corrigendum", "amendment", "circular", "notification", "pdf"]):
        return True

    return False

# ======================================================
# TAGGING (UNCHANGED)
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
# PDF LINK RESOLUTION (UNCHANGED)
# ======================================================

def resolve_pdf_url(page_url: str) -> str | None:
    if page_url.lower().endswith(".pdf"):
        return page_url

    try:
        resp = requests.get(page_url, timeout=10)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.lower().endswith(".pdf"):
                return urljoin(page_url, href)

    except Exception:
        pass

    return None

# ======================================================
# SELENIUM – SAFE SETUP (UPDATED)
# ======================================================

def setup_driver():
    options = Options()

    # 🔴 CRITICAL: prevents infinite page load hang
    options.page_load_strategy = "eager"

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    )

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.set_page_load_timeout(30)
    driver.set_script_timeout(30)

    return driver

def safe_get(driver, url: str) -> bool:
    try:
        driver.get(url)
        return True
    except TimeoutException:
        print(f"[TIMEOUT] {url}")
        try:
            driver.execute_script("window.stop();")
        except Exception:
            pass
        return False
    except WebDriverException as e:
        print(f"[DRIVER ERROR] {e}")
        return False

# ======================================================
# SCRAPERS (FIXED)
# ======================================================

def scrape_gem():
    url = "https://gem.gov.in/search/search_tender"
    entries = []
    driver = setup_driver()

    try:
        if not safe_get(driver, url):
            return entries

        time.sleep(3)

        for elem in driver.find_elements(By.XPATH, "//a[@href]"):
            title = elem.text.strip()
            href = elem.get_attribute("href")

            if not title or not is_valid_bid_update(title, href):
                continue

            entries.append({
                "title": title,
                "summary": f"GeM Regulatory / Bid Update: {title}",
                "link": href,
                "source": "GeM Portal",
                "published": datetime.utcnow().isoformat()
            })

    finally:
        driver.quit()

    return entries

def scrape_cppp():
    url = "https://eprocure.gov.in/cppp/"
    entries = []
    driver = setup_driver()

    try:
        if not safe_get(driver, url):
            return entries

        time.sleep(3)

        for elem in driver.find_elements(By.XPATH, "//a[@href]"):
            title = elem.text.strip()
            href = elem.get_attribute("href")

            if not title or not is_valid_bid_update(title, href):
                continue

            entries.append({
                "title": title,
                "summary": f"CPPP Regulatory / Bid Update: {title}",
                "link": href,
                "source": "CPP Portal",
                "published": datetime.utcnow().isoformat()
            })

    finally:
        driver.quit()

    return entries

def scrape_maharashtra_etender():
    url = "https://mahatenders.gov.in"
    entries = []
    driver = setup_driver()

    try:
        if not safe_get(driver, url):
            return entries

        time.sleep(3)

        for elem in driver.find_elements(By.XPATH, "//a[@href]"):
            title = elem.text.strip()
            href = elem.get_attribute("href")

            if not title or not is_valid_bid_update(title, href):
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
# MAIN PIPELINE (SAFE)
# ======================================================

def run_backend():
    all_entries = []

    for scraper in [scrape_gem, scrape_cppp, scrape_maharashtra_etender]:
        try:
            all_entries.extend(scraper())
        except Exception as e:
            print("[SCRAPER FAILED]", e)

    print(f"📊 TOTAL VALID RECORDS: {len(all_entries)}")

    for entry in all_entries:
        combined = f"{entry['title']} {entry['summary']}"
        pdf_url = resolve_pdf_url(entry["link"])

        payload = {
            "title": entry["title"][:500],
            "summary": entry["summary"][:2000],
            "link": entry["link"],
            "pdf_url": pdf_url,
            "source": entry["source"],
            "published_at": entry["published"],
            "content_hash": hash_content(combined),
            "tag": tag_update(combined),
            "fetched_at": datetime.utcnow().isoformat(),
        }

        supabase.table("regulation_updates") \
            .upsert(payload, on_conflict="content_hash") \
            .execute()

        print("➕ Inserted:", entry["title"][:80])

    print("✅ INGESTION COMPLETE")

# ======================================================
# ENTRY POINT
# ======================================================

if __name__ == "__main__":
    run_backend()
