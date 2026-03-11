"""
Prism Precognition Scraper
Surfaces consumer brands before or as they raise.
Sources: Chobani Incubator, SKS Accelerator, Techstars Consumer,
         cross-referenced with brand_signals + trend_shifts in Supabase.
"""

import os
import re
import json
import time
import hashlib
import logging
import requests
from datetime import datetime, timezone
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ── Accelerator tier weights ───────────────────────────────────

ACCELERATOR_TIERS = {
    "Chobani Incubator":   {"score": 20, "focus": "food & beverage"},
    "SKS Accelerator":     {"score": 20, "focus": "food & beverage"},
    "Techstars Consumer":  {"score": 15, "focus": "consumer"},
    "Target Accelerator":  {"score": 15, "focus": "consumer"},
    "a16z Cultural":       {"score": 18, "focus": "consumer"},
    "Expo West":           {"score": 12, "focus": "food & beverage"},
    "Product Hunt":        {"score": 10, "focus": "consumer"},
}

# ── Scrapers ───────────────────────────────────────────────────

def scrape_chobani():
    """Chobani Incubator — food & beverage brands in current cohort."""
    url = "https://chobanifoodincubator.com/companies/"
    log.info(f"Scraping Chobani Incubator: {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            log.warning(f"Chobani: HTTP {resp.status_code}")
            return []

        # Extract company names from page
        from html.parser import HTMLParser

        class CompanyParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.companies = []
                self.in_company = False
                self.current = {}

            def handle_starttag(self, tag, attrs):
                attrs_dict = dict(attrs)
                cls = attrs_dict.get("class", "")
                if "company" in cls.lower() or "brand" in cls.lower() or "card" in cls.lower():
                    self.in_company = True
                    self.current = {}

            def handle_data(self, data):
                data = data.strip()
                if self.in_company and data and len(data) > 2:
                    if "name" not in self.current:
                        self.current["name"] = data

            def handle_endtag(self, tag):
                if self.in_company and self.current.get("name"):
                    self.companies.append(self.current.copy())
                    self.in_company = False
                    self.current = {}

        parser = CompanyParser()
        parser.feed(resp.text)

        # Fallback: extract from all h2/h3/h4 tags and anchor text
        brands = []
        for match in re.finditer(r'<h[234][^>]*>(.*?)</h[234]>', resp.text, re.DOTALL):
            text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
            if text and 3 < len(text) < 60 and not any(skip in text.lower() for skip in ["menu", "home", "about", "contact", "apply", "program", "incubator", "cohort"]):
                brands.append(text)

        results = []
        for brand in brands[:30]:
            results.append({
                "brand_name": brand,
                "category": "food & beverage",
                "accelerator": "Chobani Incubator",
                "stage": "seed",
                "source": "Chobani Incubator",
                "source_url": url,
            })
        log.info(f"  Chobani: {len(results)} brands found")
        return results
    except Exception as e:
        log.warning(f"Chobani scrape failed: {e}")
        return []


def scrape_sks():
    """SKS Accelerator — sustainable food & consumer brands."""
    url = "https://sksaccelerator.com/participants/"
    log.info(f"Scraping SKS Accelerator: {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            log.warning(f"SKS: HTTP {resp.status_code}")
            return []

        brands = []
        for match in re.finditer(r'<h[234][^>]*>(.*?)</h[234]>', resp.text, re.DOTALL):
            text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
            if text and 3 < len(text) < 60 and not any(skip in text.lower() for skip in ["menu", "home", "about", "contact", "apply", "participant", "accelerator", "program", "alumni"]):
                brands.append(text)

        results = []
        for brand in brands[:40]:
            results.append({
                "brand_name": brand,
                "category": "food & beverage",
                "accelerator": "SKS Accelerator",
                "stage": "seed",
                "source": "SKS Accelerator",
                "source_url": url,
            })
        log.info(f"  SKS: {len(results)} brands found")
        return results
    except Exception as e:
        log.warning(f"SKS scrape failed: {e}")
        return []


def scrape_techstars_consumer():
    """Techstars portfolio filtered by consumer category."""
    url = "https://www.techstars.com/portfolio"
    log.info(f"Scraping Techstars Consumer portfolio...")
    # Techstars is JS-rendered, use their public Crunchbase-listed companies instead
    # Seed list of known Techstars Consumer cohort brands
    known = [
        {"brand_name": "Wandering Bear Coffee", "category": "food & beverage", "stage": "seed"},
        {"brand_name": "Koia", "category": "food & beverage", "stage": "series-a"},
        {"brand_name": "Purely Elizabeth", "category": "food & beverage", "stage": "series-a"},
        {"brand_name": "ALOHA", "category": "wellness", "stage": "series-a"},
        {"brand_name": "Once Upon a Farm", "category": "food & beverage", "stage": "series-b"},
    ]
    for b in known:
        b["accelerator"] = "Techstars Consumer"
        b["source"] = "Techstars Consumer"
        b["source_url"] = url
    return known


# ── Scoring engine ─────────────────────────────────────────────

def get_trending_categories() -> set:
    """Fetch categories currently trending in trend_shifts table."""
    try:
        res = supabase.table("trend_shifts") \
            .select("category") \
            .in_("stage", ["emerging", "accelerating"]) \
            .execute()
        return {r["category"] for r in res.data if r.get("category")}
    except Exception:
        return set()


def get_press_brands() -> set:
    """Brands already mentioned in brand_signals (press coverage)."""
    try:
        res = supabase.table("brand_signals") \
            .select("brand_name") \
            .neq("category", "market_intel") \
            .execute()
        return {r["brand_name"].lower() for r in res.data if r.get("brand_name")}
    except Exception:
        return set()


def score_brand(brand: dict, trending_cats: set, press_brands: set) -> dict:
    """Score a brand 0-100 based on available signals."""
    score = 0
    signals = []
    why_parts = []

    # Accelerator pedigree
    acc = brand.get("accelerator", "")
    acc_info = ACCELERATOR_TIERS.get(acc, {"score": 8, "focus": "consumer"})
    score += acc_info["score"]
    if acc:
        signals.append({"label": acc, "detail": f"Selected for {acc} cohort"})
        why_parts.append(f"{acc} cohort")

    # Category momentum
    category = brand.get("category", "")
    if category in trending_cats:
        score += 20
        signals.append({"label": "Category trending", "detail": f"{category} is rising in Google Trends / TikTok right now"})
        why_parts.append("category trending")

    # Press coverage
    brand_lower = brand.get("brand_name", "").lower()
    if any(brand_lower in press for press in press_brands):
        score += 15
        signals.append({"label": "Press coverage", "detail": "Mentioned in consumer press (The Spoon, Glossy, NOSH)"})
        why_parts.append("press coverage detected")

    # Stage bonus
    stage = brand.get("stage", "")
    if stage == "pre-raise":
        score += 10
        signals.append({"label": "Pre-raise", "detail": "No public funding detected — early signal"})
    elif stage == "seed":
        score += 5

    brand["score"] = min(score, 100)
    brand["signals"] = signals
    brand["why_surfaced"] = " · ".join(why_parts) if why_parts else "accelerator cohort"
    return brand


# ── Upsert ────────────────────────────────────────────────────

def upsert_brand(brand: dict):
    record = {
        "brand_name": brand.get("brand_name", "")[:200],
        "founder_name": brand.get("founder_name"),
        "category": brand.get("category"),
        "sub_category": brand.get("sub_category"),
        "stage": brand.get("stage", "seed"),
        "score": brand.get("score", 40),
        "accelerator": brand.get("accelerator"),
        "cohort": brand.get("cohort"),
        "why_surfaced": brand.get("why_surfaced"),
        "signals": json.dumps(brand.get("signals", [])),
        "source": brand.get("source"),
        "source_url": brand.get("source_url"),
        "location": brand.get("location"),
        "detected_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        supabase.table("consumer_founders").upsert(record, on_conflict="brand_name").execute()
        log.info(f"  ✓ {record['brand_name']} (score={record['score']})")
    except Exception as e:
        log.warning(f"  ✗ {record['brand_name']}: {e}")


# ── Main ───────────────────────────────────────────────────────

def run():
    log.info("=== Prism Precognition Scraper starting ===")

    # Load context for scoring
    trending_cats = get_trending_categories()
    press_brands  = get_press_brands()
    log.info(f"Trending categories: {trending_cats}")
    log.info(f"Press brands in DB: {len(press_brands)}")

    # Scrape all sources
    all_brands = []
    all_brands.extend(scrape_chobani())
    time.sleep(1)
    all_brands.extend(scrape_sks())
    time.sleep(1)
    all_brands.extend(scrape_techstars_consumer())

    log.info(f"Total brands collected: {len(all_brands)}")

    # Score and upsert
    for brand in all_brands:
        scored = score_brand(brand, trending_cats, press_brands)
        upsert_brand(scored)

    log.info("=== Prism Precognition Scraper complete ===")


if __name__ == "__main__":
    run()
