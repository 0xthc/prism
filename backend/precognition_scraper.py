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
    # Require unambiguous consumer product signals — no generic "health" or "fitness" (B2B software uses these too)
    CONSUMER_KW = [
        "food", "drink", "snack", "beverage", "recipe",  # food & drink
        "skincare", "haircare", "beauty", "cosmetic", "makeup", "fragrance",  # beauty
        "supplement", "vitamin", "gut health", "probiotic", "protein powder",  # wellness supplements
        "apparel", "fashion", "clothing", "streetwear", "accessories",  # fashion
        "pet food", "dog food", "cat food",  # pet
        "clean beauty", "natural deodorant", "organic",  # clean consumer
    ]
    # Reject if these appear — they indicate B2B/tech, not consumer brands
    B2B_REJECT_KW = [
        "api", "saas", "b2b", "developer", "coding", "software", "platform",
        "dashboard", "analytics", "crm", "erp", "enterprise", "startup tool",
        "data search", "database", "ai model", "llm", "copilot", "sdk", "cli",
        "chrome extension", "browser", "plugin", "productivity", "automation",
    ]
    results = []
    try:
        feed = feedparser.parse("https://www.producthunt.com/feed")
        for entry in feed.entries[:30]:
            title   = entry.get("title", "")
            summary = entry.get("summary", "")
            text    = (title + " " + summary).lower()
            if any(kw in text for kw in CONSUMER_KW) and not any(kw in text for kw in B2B_REJECT_KW):
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

def seed_tech_consumer():
    """
    Curated seed list of tech companies with consumer distribution.
    These are NOT pure brands — they're software/AI/marketplace companies
    that win through consumer experience, not brand equity.
    Think: Forerunner's current thesis (Oura, Monarch Money, Headway, Prenuvo).
    Updated: March 2026.
    """
    companies = [
        # ── Consumer AI ────────────────────────────────────────────────
        {"brand_name": "Daydream", "category": "consumer AI", "sub_category": "AI fashion", "accelerator": "Forerunner", "stage": "seed",
         "why_surfaced": "AI-native style OS — Forerunner backed · personal styling via LLM", "source_url": "https://daydream.com"},
        {"brand_name": "Nomi", "category": "consumer AI", "sub_category": "AI companion", "accelerator": "Product Hunt", "stage": "pre-raise",
         "why_surfaced": "AI companion with persistent memory — growing fast on app stores", "source_url": "https://nomi.ai"},
        {"brand_name": "Dot", "category": "consumer AI", "sub_category": "AI advisor", "accelerator": "Product Hunt", "stage": "pre-raise",
         "why_surfaced": "Personal AI trained on your life context — private, on-device", "source_url": "https://new.computer"},
        {"brand_name": "Arcade", "category": "consumer AI", "sub_category": "AI creation", "accelerator": "Forerunner", "stage": "seed",
         "why_surfaced": "Turn thoughts into things — AI-native creation platform · Forerunner backed", "source_url": "https://forerunnerventures.com/investments/arcade"},

        # ── Health Tech ─────────────────────────────────────────────────
        {"brand_name": "Superpower", "category": "health tech", "sub_category": "preventive health", "accelerator": "a16z", "stage": "seed",
         "why_surfaced": "Preventive health dashboard — bloodwork + biomarkers before symptoms · a16z backed", "source_url": "https://superpower.com"},
        {"brand_name": "Function Health", "category": "health tech", "sub_category": "lab diagnostics", "accelerator": "General Catalyst", "stage": "seed",
         "why_surfaced": "100+ lab tests annually for $499 — health data ownership trend · Mark Hyman backed", "source_url": "https://functionhealth.com"},
        {"brand_name": "January AI", "category": "health tech", "sub_category": "metabolic health", "accelerator": "First Round", "stage": "seed",
         "why_surfaced": "CGM + AI food coaching — metabolic intelligence without a prescription · First Round backed", "source_url": "https://januaryai.com"},
        {"brand_name": "Mojo", "category": "health tech", "sub_category": "men's hormone health", "accelerator": "Product Hunt", "stage": "pre-raise",
         "why_surfaced": "Testosterone optimization subscription — men's health category expanding", "source_url": "https://mojo.so"},
        {"brand_name": "Stix Health", "category": "health tech", "sub_category": "sexual health", "accelerator": "First Round", "stage": "seed",
         "why_surfaced": "At-home sexual/reproductive health delivery — millennial women · First Round backed", "source_url": "https://getstix.com"},

        # ── Longevity / Mental Health ────────────────────────────────────
        {"brand_name": "Coa", "category": "mental health", "sub_category": "mental fitness", "accelerator": "General Catalyst", "stage": "seed",
         "why_surfaced": "Mental fitness gym — proactive mental health, not reactive therapy · Gen Catalyst backed", "source_url": "https://mycoa.io"},
        {"brand_name": "Brightside Health", "category": "mental health", "sub_category": "therapy + medication", "accelerator": "a16z", "stage": "series-a",
         "why_surfaced": "Combined therapy + medication for anxiety/depression online · a16z backed", "source_url": "https://brightside.com"},
        {"brand_name": "Prenuvo", "category": "longevity", "sub_category": "full-body MRI", "accelerator": "Forerunner", "stage": "series-a",
         "why_surfaced": "Full-body MRI screening as consumer product — Forerunner + Jeff Bezos backed", "source_url": "https://prenuvo.com"},

        # ── Fintech (consumer) ──────────────────────────────────────────
        {"brand_name": "Copilot Money", "category": "fintech", "sub_category": "personal finance", "accelerator": "First Round", "stage": "seed",
         "why_surfaced": "AI-native personal finance for Apple users — premium design · First Round backed", "source_url": "https://copilot.money"},
        {"brand_name": "Monarch Money", "category": "fintech", "sub_category": "household finance", "accelerator": "Forerunner", "stage": "series-a",
         "why_surfaced": "AI-powered money management — post-Mint collapse winner · Forerunner backed", "source_url": "https://monarchmoney.com"},

        # ── Social / Community ──────────────────────────────────────────
        {"brand_name": "Locket Widget", "category": "social", "sub_category": "photo sharing", "accelerator": "YC", "stage": "series-a",
         "why_surfaced": "Lock screen photo sharing — viral Gen Z social · YC backed · #1 App Store 2022–23", "source_url": "https://locket.camera"},
        {"brand_name": "Cara", "category": "social", "sub_category": "creative community", "accelerator": "Product Hunt", "stage": "pre-raise",
         "why_surfaced": "Anti-AI social for artists — 1M users in 3 days after Adobe controversy", "source_url": "https://cara.app"},
        {"brand_name": "Peanut", "category": "social", "sub_category": "women's health community", "accelerator": "First Round", "stage": "series-a",
         "why_surfaced": "Community app for women across fertility/motherhood/menopause — 2M+ users", "source_url": "https://peanut-app.io"},

        # ── Marketplace ─────────────────────────────────────────────────
        {"brand_name": "Fora", "category": "marketplace", "sub_category": "travel agency", "accelerator": "Forerunner", "stage": "series-a",
         "why_surfaced": "Reinventing travel agency with AI — Forerunner backed · advisor + booking model", "source_url": "https://foratravel.com"},
        {"brand_name": "Archive", "category": "marketplace", "sub_category": "branded resale", "accelerator": "First Round", "stage": "series-a",
         "why_surfaced": "Branded resale platform — brands run their own secondhand market · First Round backed", "source_url": "https://archive.com"},
        {"brand_name": "Vow", "category": "marketplace", "sub_category": "wedding registry", "accelerator": "YC", "stage": "seed",
         "why_surfaced": "Modern wedding registry replacing The Knot — experience + product mix · YC backed", "source_url": "https://withjoy.com"},

        # ── Education ───────────────────────────────────────────────────
        {"brand_name": "Synthesis", "category": "education", "sub_category": "AI learning", "accelerator": "General Catalyst", "stage": "series-a",
         "why_surfaced": "AI-native problem-solving curriculum — grew out of SpaceX school for kids", "source_url": "https://synthesis.com"},
        {"brand_name": "Osmo", "category": "education", "sub_category": "kids learning", "accelerator": "a16z", "stage": "seed",
         "why_surfaced": "Physical-digital learning for ages 3-10 — a16z backed · strong retention metrics", "source_url": "https://playosmo.com"},
    ]

    for c in companies:
        c.setdefault("source", c.get("accelerator", "Manual"))
        c.setdefault("cohort", "2026")

    log.info(f"Tech consumer seed loaded: {len(companies)}")
    return companies


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
    all_brands.extend(seed_tech_consumer())
    all_brands.extend(scrape_product_hunt_consumer())

    log.info(f"Total brands collected: {len(all_brands)}")

    # Score and upsert
    for brand in all_brands:
        scored = score_brand(brand, trending_cats, press_brands)
        upsert_brand(scored)

    log.info("=== Prism Precognition Scraper complete ===")


if __name__ == "__main__":
    run()
