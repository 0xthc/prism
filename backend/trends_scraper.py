"""
Prism Trends Pipeline
Sources:
  1. Google Trends (pytrends) — rising queries by consumer category
  2. TikTok Creative Center — trending hashtags by industry
Writes to: trend_shifts table in Supabase
"""

import os
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

# ── Google Trends seed keywords per category ──────────────────
# Use specific seeds so related queries are genuinely on-topic
GTRENDS_SEEDS = {
    "beauty": [
        ["skincare routine", "serum", "moisturizer"],
        ["retinol", "niacinamide", "hyaluronic acid"],
        ["tinted sunscreen", "lip oil", "blush"],
    ],
    "food & beverage": [
        ["functional beverage", "adaptogen drink", "prebiotic soda"],
        ["protein bar", "gut health", "collagen powder"],
        ["mushroom coffee", "electrolyte drink", "matcha latte"],
    ],
    "wellness": [
        ["magnesium supplement", "ashwagandha", "sleep supplement"],
        ["creatine women", "peptide supplement", "longevity supplement"],
        ["red light therapy", "cold plunge", "breathwork"],
    ],
    "fashion": [
        ["barrel jeans", "quiet luxury", "mob wife aesthetic"],
        ["linen set", "ballet flat", "micro bag"],
        ["capsule wardrobe", "sustainable fashion brand", "vintage denim"],
    ],
}

STAGE_MAP = {
    "breakout": "emerging",
    "rising":   "accelerating",
    "top":      "mainstream",
}

# Terms that indicate noise (celebrity names, sports, news events)
NOISE_PATTERNS = [
    # Sports
    "vs ", " fc ", " city ", "inter miami", "nba", "nfl", "mlb", "nhl",
    "game", "score", "match", "championship", "tournament", "playoffs",
    # News/politics
    "election", "president", "senator", "congress", "police", "shooting",
    "earthquake", "hurricane", "storm", "weather",
    # Generic illness (not consumer)
    "norovirus", "als disease", "symptoms of ", "virus", "flu",
    # Generic names without product context
    "panarin", "artemi", "tommy paul", "stephen colletti", "wunmi",
    "karen mulder", "miss j", "golden globes", "rj decker", "alexis ortega",
    "pucci outfit",  # too celeb-specific unless we detect product
]

CONSUMER_SIGNAL_PATTERNS = [
    # Ingredients & compounds
    "acid", "serum", "retinol", "peptide", "vitamin", "collagen", "niacinamide",
    "hyaluronic", "ceramide", "bakuchiol", "gummies", "mushroom", "adaptogen",
    "probiotic", "prebiotic", "electrolyte", "creatine", "magnesium", "ashwagandha",
    # Product formats
    "balm", "cream", "lotion", "oil", "toner", "cleanser", "mask", "mist",
    "supplement", "powder", "drink", "bar", "snack", "sauce", "dressing",
    "protein", "collagen", "fiber", "whey",
    # Categories
    "sustainable", "organic", "clean", "natural", "vegan", "plant-based",
    "functional", "wellness", "beauty", "skincare", "haircare", "bodycare",
    "fashion", "jeans", "denim", "set", "outfit", "dress", "jacket",
    "gut health", "sleep", "stress", "anxiety", "focus", "energy", "recovery",
    # Consumer behaviors
    "routine", "ritual", "habit", "morning", "night", "cycle",
    "what is", "how to", "best ", "top ", "review",
]

def is_consumer_trend(term: str) -> bool:
    term_lower = term.lower()
    # Reject if noise pattern found
    if any(noise in term_lower for noise in NOISE_PATTERNS):
        return False
    # Accept if consumer signal pattern found
    if any(sig in term_lower for sig in CONSUMER_SIGNAL_PATTERNS):
        return True
    # Accept multi-word terms (more specific = more likely to be a product/ingredient)
    if len(term.split()) >= 3:
        return True
    # Reject very short single-word terms unless in consumer signal list
    if len(term.split()) == 1 and len(term) < 8:
        return False
    return True

def classify_stage(value):
    """Google Trends returns 'Breakout' string or int % change."""
    if isinstance(value, str) and value.lower() == "breakout":
        return "emerging"
    try:
        v = int(value)
        if v > 500:
            return "emerging"
        if v > 100:
            return "accelerating"
        return "mainstream"
    except Exception:
        return "accelerating"

def scrape_google_trends():
    try:
        from pytrends.request import TrendReq
    except ImportError:
        log.warning("pytrends not installed, skipping Google Trends")
        return

    pytrends = TrendReq(hl="en-US", tz=300, timeout=(10, 25), retries=2, backoff_factor=0.5)

    for category, seed_groups in GTRENDS_SEEDS.items():
        log.info(f"Google Trends — {category}...")
        seen = set()
        for seeds in seed_groups:
            try:
                pytrends.build_payload(seeds, timeframe="today 3-m", geo="US")
                related = pytrends.related_queries()

                for seed in seeds:
                    data = related.get(seed, {})
                    rising_df = data.get("rising")
                    if rising_df is None or rising_df.empty:
                        continue

                    for _, row in rising_df.head(10).iterrows():
                        term  = str(row.get("query", "")).strip()
                        value = row.get("value", 0)
                        if not term or term in seen:
                            continue
                        seen.add(term)

                        stage    = classify_stage(value)
                        momentum = min(95, int(value)) if isinstance(value, (int, float)) else 60
                        search_url = f"https://trends.google.com/trends/explore?q={term.replace(' ', '+')}&geo=US"

                        upsert_trend(
                            name=term,
                            category=category,
                            stage=stage,
                            momentum=momentum,
                            signal=f"Rising search: {value}% growth (3-month, US) — related to '{seed}'",
                            source="google_trends",
                            source_url=search_url,
                        )
                time.sleep(4)  # Google rate-limits pytrends hard
            except Exception as e:
                log.warning(f"  Google Trends [{category}] seeds={seeds} failed: {e}")
                time.sleep(6)

# ── TikTok Creative Center ─────────────────────────────────────
# Industry IDs visible in Creative Center network requests
TIKTOK_INDUSTRIES = {
    "26": "beauty",
    "18": "food & beverage",
    "22": "fashion",
    "34": "wellness",
    "29": "lifestyle",
}

TIKTOK_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/en-US",
    "Accept": "application/json, text/plain, */*",
}

TIKTOK_URL = "https://ads.tiktok.com/creative_radar_api/v1/popular_trend/hashtag/list"

def scrape_tiktok_trends():
    for industry_id, category in TIKTOK_INDUSTRIES.items():
        log.info(f"TikTok Creative Center — {category}...")
        try:
            params = {
                "period": 7,
                "page": 1,
                "limit": 20,
                "country_code": "US",
                "industry_id": industry_id,
            }
            resp = requests.get(
                TIKTOK_URL,
                params=params,
                headers=TIKTOK_HEADERS,
                timeout=15,
            )
            if resp.status_code != 200:
                log.warning(f"  TikTok {category}: HTTP {resp.status_code} — {resp.text[:200]}")
                continue

            payload = resp.json()
            log.info(f"  TikTok response keys: {list(payload.keys())}")

            # Try multiple response shapes
            data = payload.get("data", {})
            if isinstance(data, dict):
                items = data.get("list", data.get("hashtag_list", data.get("trending", [])))
            elif isinstance(data, list):
                items = data
            else:
                items = []

            if not items:
                log.warning(f"  TikTok {category}: no items in response — {str(payload)[:300]}")
                continue

            log.info(f"  TikTok {category}: {len(items)} items")

            for item in items[:15]:
                hashtag = item.get("hashtag_name", "") or item.get("name", "")
                if not hashtag:
                    continue
                hashtag = hashtag.lstrip("#")

                post_count  = item.get("publish_cnt", 0) or item.get("post_count", 0)
                view_count  = item.get("video_views", 0) or item.get("view_count", 0)
                rank        = item.get("rank", 99)
                trend_flag  = item.get("trend", "")  # "up"/"down"/"stable"

                stage = "accelerating"
                if rank <= 5:
                    stage = "emerging"
                elif rank > 15:
                    stage = "mainstream"

                momentum = max(0, min(100, 100 - rank * 4))

                signal_parts = []
                if post_count:
                    signal_parts.append(f"{_fmt_num(post_count)} posts")
                if view_count:
                    signal_parts.append(f"{_fmt_num(view_count)} views")
                if trend_flag == "up":
                    signal_parts.append("trending up")
                signal = "TikTok: " + " · ".join(signal_parts) if signal_parts else "TikTok trending"

                upsert_trend(
                    name=f"#{hashtag}",
                    category=category,
                    stage=stage,
                    momentum=momentum,
                    signal=signal,
                    source="tiktok",
                    source_url=f"https://www.tiktok.com/tag/{hashtag}",
                )
            time.sleep(1)
        except Exception as e:
            log.warning(f"  TikTok {category} failed: {e}")

def _fmt_num(n):
    n = int(n)
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.0f}K"
    return str(n)

# ── Supabase upsert ────────────────────────────────────────────

def upsert_trend(name, category, stage, momentum, signal, source, source_url):
    today = datetime.now(timezone.utc).date().isoformat()
    dedup_id = hashlib.md5(f"{name}:{source}:{today}".encode()).hexdigest()

    record = {
        "id": dedup_id,
        "trend_name": name,
        "category": category,
        "stage": stage,
        "momentum": momentum,
        "signal": signal,
        "source": source,
        "source_url": source_url,
        "detected_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        supabase.table("trend_shifts").upsert(record, on_conflict="id").execute()
        log.info(f"  Trend upserted: {name} ({category}, {stage}, momentum={momentum})")
    except Exception as e:
        log.warning(f"  Trend upsert failed for {name}: {e}")

# ── Fix trend_shifts schema for id-based dedup ────────────────

def ensure_schema():
    """Alter trend_shifts to use TEXT id for deterministic dedup."""
    # We rely on the UUID id column but pass our own hex string.
    # Supabase accepts any string as UUID if it looks like one.
    # Our MD5 hex is 32 chars — convert to UUID format.
    pass  # handled in upsert via md5 → uuid-format string

def md5_to_uuid(hex_str):
    """Convert 32-char hex to UUID format xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"""
    return f"{hex_str[0:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:32]}"

# Patch upsert to use proper UUID format
_orig_upsert = upsert_trend
def upsert_trend(name, category, stage, momentum, signal, source, source_url):
    today = datetime.now(timezone.utc).date().isoformat()
    raw_id = hashlib.md5(f"{name}:{source}:{today}".encode()).hexdigest()
    dedup_id = md5_to_uuid(raw_id)

    record = {
        "id": dedup_id,
        "trend_name": name,
        "category": category,
        "stage": stage,
        "momentum": momentum,
        "signal": signal,
        "source": source,
        "source_url": source_url,
        "detected_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        supabase.table("trend_shifts").upsert(record, on_conflict="id").execute()
        log.info(f"  ✓ {name} ({category}, {stage}, {momentum})")
    except Exception as e:
        log.warning(f"  ✗ {name}: {e}")

# ── Main ───────────────────────────────────────────────────────

def run():
    log.info("=== Prism Trends Scraper starting ===")
    scrape_tiktok_trends()   # TikTok first — fastest, no rate limit issues
    scrape_google_trends()   # Google second — needs pacing
    log.info("=== Prism Trends Scraper complete ===")

if __name__ == "__main__":
    run()
