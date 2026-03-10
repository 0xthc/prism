"""
Prism Consumer Intelligence Scraper
Runs hourly via GitHub Actions
Sources: Axios Pro Rata, TechCrunch Venture, The Spoon, Glossy, Welltodo, Product Hunt, Exploding Topics
"""

import os
import re
import json
import time
import hashlib
import logging
import feedparser
import requests
from datetime import datetime, date, timezone
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]  # service role key for writes

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── RSS Sources ────────────────────────────────────────────────

FUND_RAISE_FEEDS = [
    {"name": "Axios Pro Rata", "url": "https://www.axios.com/pro/pro-rata/feed"},
    {"name": "TechCrunch Venture", "url": "https://techcrunch.com/category/venture/feed/"},
    {"name": "Pitchbook", "url": "https://pitchbook.com/news/rss"},
    {"name": "Crunchbase News", "url": "https://news.crunchbase.com/feed/"},
]

BRAND_SIGNAL_FEEDS = [
    {"name": "The Spoon", "url": "https://thespoon.tech/feed/", "category": "food & beverage"},
    {"name": "Glossy", "url": "https://www.glossy.co/feed", "category": "beauty & fashion"},
    {"name": "Welltodo", "url": "https://www.welltodoglobal.com/feed/", "category": "wellness"},
    {"name": "Vegconomist", "url": "https://vegconomist.com/feed/", "category": "food & beverage"},
    {"name": "NOSH", "url": "https://nosh.com/news/feed/rss/", "category": "food & beverage"},
]

CONSUMER_VC_FEEDS = [
    {"name": "Consumer VC", "url": "https://www.theconsumervc.com/feed"},
    {"name": "Forerunner Blog", "url": "https://www.forerunnerventures.com/blog/feed"},
]

# ── Fund raise detection keywords ─────────────────────────────

CONSUMER_KEYWORDS = [
    "consumer", "d2c", "direct-to-consumer", "cpg", "brand", "wellness",
    "beauty", "food", "beverage", "fashion", "retail", "longevity",
    "femtech", "health", "skincare", "supplement", "pet", "baby",
    "home", "lifestyle", "fitness", "mental health", "sleep",
]

FUND_KEYWORDS = [
    "fund", "raises", "closes", "million", "venture", "capital",
    "seed fund", "new fund", "first close", "final close", "lp",
]

CATEGORY_MAP = {
    "longevity": ["longevity", "anti-aging", "healthspan", "lifespan", "aging"],
    "beauty": ["beauty", "skincare", "cosmetic", "makeup", "haircare"],
    "wellness": ["wellness", "mental health", "sleep", "stress", "mindfulness", "meditation"],
    "food & beverage": ["food", "beverage", "drink", "snack", "nutrition", "functional food"],
    "femtech": ["femtech", "women's health", "fertility", "menopause", "period"],
    "pet": ["pet", "dog", "cat", "animal"],
    "fitness": ["fitness", "workout", "gym", "athletic", "sport"],
    "home & living": ["home", "interior", "furniture", "clean", "sustainable home"],
    "fashion": ["fashion", "apparel", "clothing", "accessories", "luxury"],
    "sustainability": ["sustainable", "climate", "eco", "green", "circular"],
}

def detect_categories(text: str) -> list[str]:
    text_lower = text.lower()
    detected = []
    for category, keywords in CATEGORY_MAP.items():
        if any(kw in text_lower for kw in keywords):
            detected.append(category)
    return detected or ["consumer"]

def extract_fund_size(text: str) -> int | None:
    """Extract fund size in millions from text."""
    patterns = [
        r"\$(\d+(?:\.\d+)?)\s*billion",
        r"\$(\d+(?:\.\d+)?)\s*B\b",
        r"\$(\d+(?:\.\d+)?)\s*million",
        r"\$(\d+(?:\.\d+)?)\s*M\b",
    ]
    for i, pattern in enumerate(patterns):
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            if i <= 1:  # billion
                return int(val * 1000)
            return int(val)
    return None

def is_consumer_fund_raise(title: str, summary: str) -> bool:
    text = (title + " " + summary).lower()
    has_consumer = any(kw in text for kw in CONSUMER_KEYWORDS)
    has_fund = any(kw in text for kw in FUND_KEYWORDS)
    return has_consumer and has_fund

def upsert_fund_raise(entry: dict, source: str):
    title = entry.get("title", "")
    summary = entry.get("summary", "") or entry.get("description", "")
    text = title + " " + summary
    link = entry.get("link", "")
    
    # Try to parse date
    try:
        published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).date()
    except Exception:
        published = date.today()

    fund_size = extract_fund_size(text)
    categories = detect_categories(text)

    # Extract GP/fund name from title (best effort)
    fund_name = title[:100] if title else "Unknown"

    record = {
        "fund_name": fund_name,
        "thesis": summary[:500] if summary else title,
        "categories": categories,
        "fund_size_m": fund_size,
        "announced_date": published.isoformat(),
        "source_url": link,
        "source": source,
        "lp_signal": None,
        "watch": None,
    }

    try:
        supabase.table("fund_raises").upsert(record, on_conflict="fund_name,announced_date").execute()
        log.info(f"Fund raise upserted: {fund_name}")
    except Exception as e:
        log.warning(f"Fund raise upsert failed: {e}")

def upsert_brand_signal(entry: dict, category: str, source: str):
    title = entry.get("title", "")
    summary = entry.get("summary", "") or entry.get("description", "")
    link = entry.get("link", "")
    today = date.today().isoformat()

    record = {
        "brand_name": title[:200],
        "category": category,
        "what": summary[:500] if summary else title,
        "signal_type": "rss",
        "source_url": link,
        "detected_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        supabase.table("brand_signals").upsert(record, on_conflict="brand_name,detected_at::DATE").execute()
        log.info(f"Brand signal upserted: {title[:50]}")
    except Exception as e:
        log.warning(f"Brand signal upsert failed: {e}")

# ── Product Hunt scraper ───────────────────────────────────────

CONSUMER_PH_TOPICS = ["health-and-fitness", "food-and-drink", "beauty", "wellness", "lifestyle"]

def scrape_product_hunt():
    """Fetch top consumer launches from Product Hunt RSS."""
    feed_url = "https://www.producthunt.com/feed"
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:20]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            text = (title + " " + summary).lower()
            is_consumer = any(kw in text for kw in CONSUMER_KEYWORDS)
            if is_consumer:
                upsert_brand_signal(entry, detect_categories(text)[0], "product_hunt")
    except Exception as e:
        log.warning(f"Product Hunt scrape failed: {e}")

# ── Main pipeline ──────────────────────────────────────────────

def run():
    log.info("Prism scraper starting...")

    # 1. Scrape fund raises
    for feed_def in FUND_RAISE_FEEDS + CONSUMER_VC_FEEDS:
        log.info(f"Scraping {feed_def['name']}...")
        try:
            feed = feedparser.parse(feed_def["url"])
            for entry in feed.entries[:10]:
                title = entry.get("title", "")
                summary = entry.get("summary", "") or entry.get("description", "")
                if is_consumer_fund_raise(title, summary):
                    upsert_fund_raise(entry, feed_def["name"])
        except Exception as e:
            log.warning(f"Feed {feed_def['name']} failed: {e}")
        time.sleep(1)

    # 2. Scrape brand signals
    for feed_def in BRAND_SIGNAL_FEEDS:
        log.info(f"Scraping {feed_def['name']}...")
        try:
            feed = feedparser.parse(feed_def["url"])
            for entry in feed.entries[:10]:
                upsert_brand_signal(entry, feed_def["category"], feed_def["name"])
        except Exception as e:
            log.warning(f"Feed {feed_def['name']} failed: {e}")
        time.sleep(1)

    # 3. Product Hunt consumer launches
    log.info("Scraping Product Hunt...")
    scrape_product_hunt()

    log.info("Prism scraper complete.")

if __name__ == "__main__":
    run()
