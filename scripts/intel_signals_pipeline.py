#!/usr/bin/env python3
"""
Prism — Intel + Signals RSS Pipeline
Pulls RSS feeds, classifies each item via Gemini,
routes to intel_items or signals_v2 in Supabase.
Run daily via GitHub Actions cron.
"""

import os, json, time, hashlib, requests
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

GEMINI_KEY = os.environ.get("GEMINI_KEY", "AIzaSyAlsqt4U2oBt4qITuxD4utwm4zqu8S6y0g")
SUPABASE_URL = "https://datqjbnetudvqjsxjczl.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRhdHFqYm5ldHVkdnFqc3hqY3psIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE5NjMxMTIsImV4cCI6MjA4NzUzOTExMn0.8QY1ew74ahBLmhU5vAyZF-ygRGr0p4xpM8i0OLTV4-4")

RSS_FEEDS = [
    # Deals & funding
    {"url": "https://techcrunch.com/category/startups/feed/", "source": "TechCrunch"},
    {"url": "https://www.axios.com/feeds/feed.rss", "source": "Axios"},
    # CPG / consumer trade
    {"url": "https://www.bevnet.com/feed/", "source": "BevNET"},
    {"url": "https://www.nosh.com/feed/", "source": "NOSH"},
    {"url": "https://www.beautyindependent.com/feed/", "source": "Beauty Independent"},
    {"url": "https://www.retaildive.com/feeds/news/", "source": "Retail Dive"},
    {"url": "https://www.modernretail.co/feed/", "source": "Modern Retail"},
    {"url": "https://wwd.com/feed/", "source": "WWD"},
    # Regulatory
    {"url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/press-releases/rss.xml", "source": "FDA"},
    # Newsletters / consumer intel
    {"url": "https://www.2pml.com/feed", "source": "2PM"},
    {"url": "https://retailbrew.beehiiv.com/feed", "source": "Retail Brew"},
]

CONSUMER_CATEGORIES = [
    "Food & Beverage", "Functional Food & Bev", "Beauty & Skincare",
    "Wellness & Supplements", "Fitness & Sports", "Mental Health & Wellness Tech",
    "Fashion & Apparel", "Pet", "Home & Living", "Baby & Family",
    "Personal Care & Hygiene", "Consumer Health & Telehealth",
    "Sustainability & Eco", "Consumer Tech & Wearables", "Food Service & Hospitality",
]

def gemini(prompt, retries=3):
    for attempt in range(retries):
        try:
            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}",
                headers={"Content-Type": "application/json"},
                json={"contents": [{"parts": [{"text": prompt}]}],
                      "generationConfig": {"temperature": 0.1, "maxOutputTokens": 512}},
                timeout=30
            )
            d = resp.json()
            if "error" in d:
                if "quota" in d["error"]["message"].lower():
                    print(f"  Quota hit, waiting 60s (attempt {attempt+1})")
                    time.sleep(60)
                    continue
                raise Exception(d["error"]["message"])
            return d["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(5)
            else:
                raise
    raise Exception("All retries failed")

def fetch_rss(url):
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0 (Prism/1.0)"})
        root = ET.fromstring(r.content)
        items = []
        # Handle both RSS and Atom
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for item in root.findall(".//item") + root.findall(".//atom:entry", ns):
            title = item.findtext("title") or item.findtext("atom:title", namespaces=ns) or ""
            link = item.findtext("link") or item.findtext("atom:link", namespaces=ns) or ""
            desc = item.findtext("description") or item.findtext("atom:summary", namespaces=ns) or ""
            pubdate = item.findtext("pubDate") or item.findtext("atom:published", namespaces=ns) or ""
            if title:
                items.append({"title": title.strip(), "link": link.strip(), "description": desc[:500], "pubdate": pubdate})
        return items[:20]  # max 20 per feed
    except Exception as e:
        print(f"  RSS fetch error {url}: {e}")
        return []

def classify_item(title, description, source):
    cats = "\n".join(f"- {c}" for c in CONSUMER_CATEGORIES)
    prompt = f"""You are classifying news items for a consumer VC intelligence platform.

Article: "{title}"
Source: {source}
Summary: {description[:300]}

Answer these questions in JSON format only:
{{
  "is_consumer_relevant": true/false,
  "destination": "intel" or "signal" or "skip",
  "stream_type": "deals" or "regulatory" or "research" or "retail" or null,
  "category": one of the categories below or null,
  "deal_size_tier": "<$10M" or "$10-100M" or "$100M-1B" or "$1B+" or null,
  "context_line": "one sentence on why this matters for consumer investing" or null,
  "maturity": "early" or "heating" or "peaking" or null
}}

Categories:
{cats}

Rules:
- "intel": market events (M&A, funding rounds, regulatory decisions, major retail expansions)
- "signal": emerging trends, new ingredients, new behaviors, early-stage brand launches
- "skip": not relevant to consumer investing (pure tech, politics, sports, etc.)
- Only classify as consumer_relevant if directly relevant to consumer goods/brands/investing

Return ONLY valid JSON, no explanation."""

    result = gemini(prompt)
    result = result.strip().strip("```json").strip("```").strip()
    try:
        return json.loads(result)
    except:
        return {"is_consumer_relevant": False, "destination": "skip"}

def item_id(title, source):
    return hashlib.md5(f"{title}{source}".encode()).hexdigest()[:16]

def check_exists(table, ext_id):
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/{table}?source_name=eq.{ext_id}&limit=1",
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )
    return len(resp.json()) > 0

def insert_intel(item):
    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/intel_items",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        },
        json=item
    )
    return resp.status_code

def insert_signal(item):
    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/signals_v2",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        },
        json=item
    )
    return resp.status_code

def main():
    print(f"Prism Intel+Signals pipeline — {datetime.now().isoformat()}\n")
    
    intel_count = 0
    signal_count = 0
    skip_count = 0
    
    for feed in RSS_FEEDS:
        print(f"→ {feed['source']}")
        items = fetch_rss(feed["url"])
        print(f"  {len(items)} items fetched")
        
        for rss_item in items:
            title = rss_item["title"]
            if not title or len(title) < 10:
                continue
            
            time.sleep(2)  # rate limit
            
            try:
                cls = classify_item(title, rss_item["description"], feed["source"])
            except Exception as e:
                print(f"  classify error: {e}")
                continue
            
            if not cls.get("is_consumer_relevant") or cls.get("destination") == "skip":
                skip_count += 1
                continue
            
            dest = cls.get("destination")
            
            if dest == "intel":
                record = {
                    "headline": title[:200],
                    "stream_type": cls.get("stream_type") or "deals",
                    "category": cls.get("category") or "Food & Beverage",
                    "deal_size_tier": cls.get("deal_size_tier"),
                    "context_line": cls.get("context_line") or "",
                    "source_url": rss_item["link"],
                    "source_name": feed["source"],
                    "published_at": datetime.now(timezone.utc).date().isoformat(),
                    "notes": "",
                }
                status = insert_intel(record)
                if status in (200, 201):
                    intel_count += 1
                    print(f"  ✓ INTEL: {title[:60]}")
                else:
                    print(f"  ✗ insert failed ({status}): {title[:60]}")
            
            elif dest == "signal":
                record = {
                    "name": title[:100],
                    "type": "trend",
                    "category": (cls.get("category") or "Food & Beverage").lower().replace(" & ", " ").split()[0],
                    "maturity": cls.get("maturity") or "early",
                    "signal_strength": 2,
                    "first_spotted": datetime.now(timezone.utc).date().isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "sources": [{"label": feed["source"], "url": rss_item["link"]}],
                    "notes": cls.get("context_line") or "",
                    "trajectory_description": "",
                    "is_weekly_pick": False,
                }
                status = insert_signal(record)
                if status in (200, 201):
                    signal_count += 1
                    print(f"  ✓ SIGNAL: {title[:60]}")
                else:
                    print(f"  ✗ insert failed ({status}): {title[:60]}")
        
        time.sleep(3)
    
    print(f"\n✓ Done — Intel: {intel_count} | Signals: {signal_count} | Skipped: {skip_count}")

if __name__ == "__main__":
    main()
