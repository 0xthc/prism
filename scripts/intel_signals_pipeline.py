#!/usr/bin/env python3
"""
Prism — Intel + Signals RSS Pipeline
Pulls RSS feeds, classifies each item via keyword matching (no API needed).
Routes to intel_items or signals_v2 in Supabase.
Run daily via GitHub Actions cron.
"""

import os, json, time, hashlib, requests, re
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

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

# ── Keyword classifier (no API needed) ───────────────────────────────────────

CATEGORY_KEYWORDS = {
    "Beauty & Skincare":          ["beauty","skincare","skin care","serum","moisturizer","makeup","cosmetic","lipstick","hair care","haircare","nail","sunscreen","spf","retinol","collagen","cleanser","toner","foundation","mascara","fragrance","perfume","glossier","drunk elephant","topicals","eadem","youthforia","krave","tatcha","olaplex","rare beauty","ilia","fenty","byoma","versed","hero cosmetics","curology","prose","aesop","augustinus","kinlo","rhode","charlotte tilbury","ilia beauty","kosas","nécessaire"],
    "Functional Food & Bev":      ["prebiotic","probiotic","adaptogen","olipop","poppi","recess","ghia","hiyo","grüns","grun","ag1","liquid iv","nuun","bai","spindrift","lmnt","mid-day squares","hu kitchen","rxbar","bulletproof","four sigmatic","mud wtr","sunwink","kombucha","kefir","electrolyte","mushroom drink","nootropic","functional beverage","gut health drink","microbiome drink","deux","kin euphorics","within","non-alcoholic","non-alc","zero proof","alcohol-free"],
    "Food & Beverage":            ["food","snack","beverage","cpg","consumer packaged goods","drink","coffee","tea","juice","sauce","pasta","bread","cereal","cookie","chip","protein bar","meal kit","farm","dairy","yogurt","ice cream","chocolate","candy","bakery","smoothie","frozen food","grocery","organic food","vegan food","sweetgreen","daily harvest","sakara","vital farms","siete","banza","chomps","chobani","oatly","califia","harvest snaps","halo top","liquid death","fly by jing","laoban"],
    "Wellness & Supplements":     ["supplement","vitamin","mineral","ashwagandha","turmeric","cbd","hemp","melatonin","magnesium","collagen supplement","biotin","gummy vitamin","gummies","capsule","ritual","care/of","thorne","olly","create wellness","seed probiotic","rootine","youtheory","garden of life","new chapter","nature made"],
    "Fitness & Sports":           ["fitness","gym","yoga","running","cycling","athletic wear","performance","peloton","tonal","hydrow","lululemon","vuori","gymshark","nobull","rucking","goruck","outdoor voices","mirror fitness","equinox","sweaty betty","crossfit","strength training"],
    "Fashion & Apparel":          ["fashion","apparel","clothing","activewear","swimwear","footwear","sneaker","handbag","jewelry","warby parker","everlane","away luggage","allbirds","skims","madhappy","kith","cotopaxi","pact","reformation","birkenstock","ganni","highsnobiety","sporty & rich"],
    "Home & Living":              ["home goods","home decor","furniture","candle","bedding","mattress","cookware","kitchen","cleaning product","casper","parachute","great jones","our place","grove collaborative","blueland","caraway","equal parts","coyuchi","boll & branch"],
    "Consumer Health & Telehealth":["telehealth","telemedicine","hims","hers","ro health","noom","fertility","menopause","cgm","continuous glucose","everlywell","function health","getlabs","dexcom","keeps","musely","cerebral","men's health","women's health","direct to consumer health"],
    "Mental Health & Wellness Tech":["mental health","therapy app","meditation app","mindfulness","sleep app","anxiety","calm app","headspace","betterhelp","talkspace","woebot","cerebral","brightside"],
    "Pet":                        ["pet food","dog food","cat food","pet care","rover","wag","chewy","nom nom","ollie","farmer's dog","open farm","pet supplement"],
    "Baby & Family":              ["baby food","infant formula","toddler snack","children's","family brand","once upon a farm","little spoon","yumi","lovevery","cerebelly","pipette"],
    "Sustainability & Eco":       ["sustainable brand","sustainable fashion","sustainable food","eco-friendly","recycled","carbon neutral","climate","zero waste","circular economy","resale","secondhand","patagonia","tentree","outerknown","allbirds sustainability","cotopaxi impact"],
    "Consumer Tech & Wearables":  ["wearable","smart ring","oura","whoop","levels health","cgm wearable","withings","strava","fitness tracker","health wearable"],
    "Food Service & Hospitality": ["restaurant chain","fast casual","food delivery","sweetgreen expansion","shake shack","kopi kenangan","hospitality brand"],
    "Personal Care & Hygiene":    ["deodorant","toothpaste","shampoo","conditioner","body wash","oral care","dental","razor","native deodorant","by humankind","quip","cocofloss","soapbox","primally pure"],
}

INTEL_TRIGGERS = [
    r"\$[\d,.]+\s*(million|billion|m\b|b\b)",  # money amounts
    r"\bacquir\w+\b",                            # acquires / acquired / acquisition
    r"\braise[sd]?\b.*\$",                       # raised $
    r"\bround\b.*\$",                            # round of $
    r"\bseries [a-e]\b",                         # Series A/B/C
    r"\bfda\b",                                  # FDA
    r"\bfunding\b",                              # funding
    r"\bipO\b|\binitial public\b",               # IPO
    r"\bmerger\b|\bmerge[sd]?\b",                # merger
    r"\bpartnership\b",                          # partnership
    r"\blaunche[sd]?\b",                         # launched
    r"\bexpan[sd]\w*\b",                         # expand/expansion
    r"\bregulat\w+\b",                           # regulatory
    r"\blaw ?suit\b|\blitigation\b",             # legal
    r"\bstores?\b",                              # retail expansion
    r"\bwholesale\b|\bretail\b",                 # retail
]

SIGNAL_TRIGGERS = [
    r"\btrend\b|\btrending\b",
    r"\bemerging\b|\bemerge[sd]?\b",
    r"\bingredient\b",
    r"\bbehavior\b|\bbehaviour\b",
    r"\bgen z\b|\bmillennial\b",
    r"\bconsumer shift\b|\bconsumer behavior\b",
    r"\bnew category\b|\bnew format\b",
    r"\bviral\b|\bvirality\b",
    r"\btiktok\b|\binstagram\b",
    r"\bsearch\b.*\bup\b|\bsearch\b.*\bgrow\b",
    r"\blaunch\w*\b",
    r"\bminimali[sz]m\b|\bclean label\b|\btransparency\b",
]

SKIP_KEYWORDS = ["politics","election","war","military","ukraine","russia","china policy","immigration","senate","congress","republican","democrat","nba","nfl","nhl","mlb","soccer","football","cricket","olympic","esport","gaming","crypto","bitcoin","ethereum","blockchain","nft","metaverse","space","nasa","quantum","semiconductor","defense","cybersecurity","b2b saas","enterprise software","developer tool","cloud infrastructure"]

def classify_item(title, description, source):
    """Keyword-based classifier — no API required."""
    text = (title + " " + description).lower()
    
    # Hard skip
    if any(kw in text for kw in SKIP_KEYWORDS):
        return {"is_consumer_relevant": False, "destination": "skip"}
    
    # Detect category
    cat_scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            cat_scores[cat] = score
    
    if not cat_scores:
        return {"is_consumer_relevant": False, "destination": "skip"}
    
    best_cat = max(cat_scores, key=cat_scores.get)
    
    # Intel vs signal
    is_intel = any(re.search(pat, text, re.I) for pat in INTEL_TRIGGERS)
    is_signal = any(re.search(pat, text, re.I) for pat in SIGNAL_TRIGGERS)
    
    # Determine stream_type for intel
    stream_type = "deals"
    if re.search(r"\bfda\b|\bregulat\w+\b|\blaw\b|\bban\b|\bapproval\b", text, re.I):
        stream_type = "regulatory"
    elif re.search(r"\bstudy\b|\bresearch\b|\bclinical\b|\btrial\b|\bscientific\b", text, re.I):
        stream_type = "research"
    elif re.search(r"\bretail\b|\bstore\b|\bwholesale\b|\bsupermarket\b|\bwhole foods\b|\btarget\b|\bwalmart\b", text, re.I):
        stream_type = "retail"
    
    # Deal size
    deal_size = None
    m = re.search(r"\$([\d,.]+)\s*(billion|million|b\b|m\b)", text, re.I)
    if m:
        val = float(m.group(1).replace(",",""))
        unit = m.group(2).lower()
        if "b" in unit:
            val *= 1000
        if val >= 1000: deal_size = "$1B+"
        elif val >= 100: deal_size = "$100M-1B"
        elif val >= 10: deal_size = "$10-100M"
        else: deal_size = "<$10M"
    
    # Maturity for signals
    maturity = "early"
    if re.search(r"\bmainstream\b|\beverywhere\b|\bpeaking\b|\bsaturated\b", text, re.I):
        maturity = "peaking"
    elif re.search(r"\bgrowing\b|\bheating\b|\bmomentum\b|\baccelerating\b|\bexplosive\b", text, re.I):
        maturity = "heating"
    
    if is_intel:
        return {
            "is_consumer_relevant": True,
            "destination": "intel",
            "stream_type": stream_type,
            "category": best_cat,
            "deal_size_tier": deal_size,
            "context_line": None,
            "maturity": None,
        }
    elif is_signal:
        return {
            "is_consumer_relevant": True,
            "destination": "signal",
            "stream_type": None,
            "category": best_cat,
            "deal_size_tier": None,
            "context_line": None,
            "maturity": maturity,
        }
    else:
        return {"is_consumer_relevant": False, "destination": "skip"}

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
