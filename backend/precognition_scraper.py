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

def seed_accelerator_brands():
    """
    Curated seed list of real brands from major consumer accelerators.
    Sites are JS-rendered and not directly scrapable — maintained manually.
    Updated: March 2026.
    """
    brands = [
        # ── Chobani Incubator (food & beverage focus) ──────────────────
        {"brand_name": "Slate Milk", "category": "food & beverage", "sub_category": "functional dairy", "accelerator": "Chobani Incubator", "stage": "seed"},
        {"brand_name": "Tosi", "category": "food & beverage", "sub_category": "snack bars", "accelerator": "Chobani Incubator", "stage": "seed"},
        {"brand_name": "Tia Lupita", "category": "food & beverage", "sub_category": "sauces", "accelerator": "Chobani Incubator", "stage": "seed"},
        {"brand_name": "Moku Foods", "category": "food & beverage", "sub_category": "plant-based", "accelerator": "Chobani Incubator", "stage": "seed"},
        {"brand_name": "Créme de la Créme", "category": "food & beverage", "sub_category": "ice cream", "accelerator": "Chobani Incubator", "stage": "pre-raise"},
        {"brand_name": "Mid-Day Squares", "category": "food & beverage", "sub_category": "functional chocolate", "accelerator": "Chobani Incubator", "stage": "seed"},
        # Removed: Goodles (well-known), Fly by Jing (Series A established), Partake Foods (Series A established), Yumi (Series A established)

        # ── SKS Accelerator (sustainable consumer) ─────────────────────
        {"brand_name": "Loliware", "category": "sustainability", "sub_category": "packaging", "accelerator": "SKS Accelerator", "stage": "seed"},
        {"brand_name": "Foodshed", "category": "food & beverage", "sub_category": "local supply chain", "accelerator": "SKS Accelerator", "stage": "pre-raise"},
        {"brand_name": "Bucha Brewers", "category": "food & beverage", "sub_category": "kombucha", "accelerator": "SKS Accelerator", "stage": "seed"},
        # Removed: Barnana (established), Meati Foods (Series B)

        # ── Techstars Consumer ──────────────────────────────────────────
        {"brand_name": "Wandering Bear Coffee", "category": "food & beverage", "sub_category": "cold brew", "accelerator": "Techstars Consumer", "stage": "seed"},
        {"brand_name": "Koia", "category": "food & beverage", "sub_category": "plant protein", "accelerator": "Techstars Consumer", "stage": "series-a"},
        # Removed: Purely Elizabeth (acquired by Post Holdings), ALOHA (established), Once Upon a Farm (Series B)

        # ── Target Accelerator ──────────────────────────────────────────
        {"brand_name": "Live Más Skincare", "category": "beauty", "sub_category": "latina-founded", "accelerator": "Target Accelerator", "stage": "pre-raise"},
        {"brand_name": "Base Coat", "category": "beauty", "sub_category": "nail care", "accelerator": "Target Accelerator", "stage": "seed"},
        {"brand_name": "Crown Affair", "category": "beauty", "sub_category": "haircare", "accelerator": "Target Accelerator", "stage": "seed"},
        # Removed: Siete Family Foods (acquired by PepsiCo for $1.2B)

        # ── Expo West 2026 (new brands from the show floor) ────────────
        {"brand_name": "It's Skinny", "category": "food & beverage", "sub_category": "low-calorie pasta", "accelerator": "Expo West", "stage": "seed", "cohort": "2026"},
        {"brand_name": "Sach Foods", "category": "food & beverage", "sub_category": "south asian", "accelerator": "Expo West", "stage": "pre-raise", "cohort": "2026"},
        {"brand_name": "Sunup Oats", "category": "food & beverage", "sub_category": "functional oats", "accelerator": "Expo West", "stage": "pre-raise", "cohort": "2026"},
        {"brand_name": "HEYBAR", "category": "food & beverage", "sub_category": "plant protein", "accelerator": "Expo West", "stage": "pre-raise", "cohort": "2026"},
        {"brand_name": "Morinaga My/Mochi", "category": "food & beverage", "sub_category": "ice cream", "accelerator": "Expo West", "stage": "series-a", "cohort": "2026"},
    ]

    url_map = {
        "Chobani Incubator":  "https://www.chobani.com/impact/incubator",
        "SKS Accelerator":    "https://sksaccelerator.com",
        "Techstars Consumer": "https://www.techstars.com/portfolio",
        "Target Accelerator": "https://corporate.target.com/sustainability-governance/society/target-forward/accelerators",
        "Expo West":          "https://www.expowest.com",
    }

    for b in brands:
        b["source"] = b.get("accelerator", "Manual")
        b["source_url"] = url_map.get(b.get("accelerator", ""), "")

    log.info(f"Seed brands loaded: {len(brands)}")
    return brands


def scrape_product_hunt_consumer():
    """Product Hunt RSS — consumer launches in the last 7 days."""
    import feedparser
    log.info("Scraping Product Hunt for consumer launches...")
    CONSUMER_KW = ["food", "drink", "beauty", "wellness", "health", "fitness",
                   "skincare", "supplement", "beverage", "fashion", "lifestyle",
                   "sleep", "gut", "protein", "snack", "clean", "natural"]
    results = []
    try:
        feed = feedparser.parse("https://www.producthunt.com/feed")
        for entry in feed.entries[:30]:
            title   = entry.get("title", "")
            summary = entry.get("summary", "")
            text    = (title + " " + summary).lower()
            if any(kw in text for kw in CONSUMER_KW):
                cat = "consumer"
                for kw in ["food", "drink", "snack", "beverage"]:
                    if kw in text: cat = "food & beverage"; break
                for kw in ["beauty", "skincare", "haircare"]:
                    if kw in text: cat = "beauty"; break
                for kw in ["wellness", "supplement", "health", "sleep", "gut"]:
                    if kw in text: cat = "wellness"; break
                for kw in ["fashion", "style", "apparel"]:
                    if kw in text: cat = "fashion"; break
                results.append({
                    "brand_name": title[:100],
                    "category": cat,
                    "accelerator": "Product Hunt",
                    "stage": "pre-raise",
                    "source": "Product Hunt",
                    "source_url": entry.get("link", ""),
                })
        log.info(f"  Product Hunt: {len(results)} consumer launches")
    except Exception as e:
        log.warning(f"Product Hunt scrape failed: {e}")
    return results


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

    # Collect brands from all sources
    all_brands = []
    all_brands.extend(seed_accelerator_brands())
    all_brands.extend(scrape_product_hunt_consumer())

    log.info(f"Total brands collected: {len(all_brands)}")

    # Score and upsert
    for brand in all_brands:
        scored = score_brand(brand, trending_cats, press_brands)
        upsert_brand(scored)

    log.info("=== Prism Precognition Scraper complete ===")


if __name__ == "__main__":
    run()
