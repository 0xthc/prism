#!/usr/bin/env python3
"""
Prism — Portfolio Scraper (Jina.ai reader + HTML fallback)
Scrapes fund portfolio pages via r.jina.ai (handles JS rendering remotely),
extracts company names, sector, status, exit info.
Run: python3 scripts/scrape_portfolios_playwright.py
"""

import os, re, time, requests
from datetime import datetime

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://datqjbnetudvqjsxjczl.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRhdHFqYm5ldHVkdnFqc3hqY3psIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE5NjMxMTIsImV4cCI6MjA4NzUzOTExMn0.8QY1ew74ahBLmhU5vAyZF-ygRGr0p4xpM8i0OLTV4-4")

# ── Category classifier ───────────────────────────────────────────────────────

CATEGORY_MAP = {
    "Beauty & Skincare":            ["beauty","skincare","skin care","cosmetic","makeup","serum","moisturizer","hair care","haircare","fragrance","perfume","sunscreen","spf","nail","glossier","topicals","krave","tatcha","drunk elephant","olaplex","rare beauty","ilia","fenty","byoma","versed","hero cosmetics","curology","prose","aesop","augustinus","kinlo","rhode","charlotte tilbury","kosas","nécessaire","eadem","crown affair","ourself","snif","youthforia","birchbox","beautystat","biologica","caliray","cay skin","dieux","feals","iris & romeo","jupiter","k18","kinship","kinship skin","lashify","may lindstrom","merit","naturium","olaplex","osea","onda","saie","summer fridays","supergoop","tula","versed","violet grey","veil cosmetics","kulfi"],
    "Functional Food & Bev":        ["prebiotic","probiotic","adaptogen","functional bev","gut health","electrolyte","nootropic","kombucha","kefir","mushroom drink","non-alcoholic","non-alc","zero proof","olipop","poppi","recess","ghia","hiyo","grüns","ag1","liquid iv","nuun","spindrift","lmnt","mid-day squares","kin euphorics","deux","health-ade","sunwink","mud/wtr","four sigmatic","bulletproof","deux","arrae","javvy"],
    "Food & Beverage":              ["food","snack","beverage","cpg","drink","coffee","tea","juice","sauce","pasta","cereal","cookie","chip","bar","meal kit","farm","dairy","yogurt","ice cream","chocolate","candy","bakery","smoothie","frozen","grocery","organic food","vegan","sweetgreen","daily harvest","sakara","vital farms","siete","banza","chomps","chobani","oatly","califia","harvest snaps","halo top","liquid death","fly by jing","laoban","magic spoon","marley spoon","hint","spindrift","ollie","ample hills","birchbox"],
    "Wellness & Supplements":       ["supplement","vitamin","mineral","ashwagandha","turmeric","cbd","melatonin","magnesium","collagen supplement","biotin","gummy","ritual","care/of","thorne","olly","create wellness","seed probiotic","rootine","garden of life","new chapter","oneskin","one skin"],
    "Fitness & Sports":             ["fitness","gym","yoga","running","cycling","athletic wear","peloton","tonal","hydrow","lululemon","vuori","gymshark","nobull","rucking","goruck","outdoor voices","mirror fitness","equinox","sweaty betty"],
    "Fashion & Apparel":            ["fashion","apparel","clothing","activewear","footwear","sneaker","handbag","jewelry","warby parker","everlane","away","allbirds","skims","madhappy","kith","cotopaxi","pact","reformation","birkenstock","ganni","highsnobiety","chubbies","birdies","stadium goods","bonobos","evolvetogether"],
    "Home & Living":                ["home goods","decor","furniture","candle","bedding","mattress","cookware","kitchen","cleaning","casper","parachute","great jones","our place","grove","blueland","caraway","equal parts","coyuchi","boll & branch","neighborhood goods"],
    "Consumer Health & Telehealth": ["telehealth","telemedicine","hims","hers","ro health","noom","fertility","menopause","cgm","everlywell","function health","getlabs","dexcom","keeps","musely","oscar health","k health","heartbeat health","winx","perelel"],
    "Mental Health & Wellness Tech":["mental health","therapy app","meditation","mindfulness","sleep","anxiety","calm app","headspace","betterhelp","talkspace","woebot","cerebral","brightside"],
    "Pet":                          ["pet food","dog food","cat food","pet care","rover","wag","chewy","nom nom","ollie pet","farmer's dog","open farm","barkbox","native pet"],
    "Baby & Family":                ["baby food","infant","toddler","children's","once upon a farm","little spoon","yumi","lovevery","rockets of awesome"],
    "Sustainability & Eco":         ["sustainable","eco-friendly","recycled","carbon neutral","climate","zero waste","circular","resale","patagonia","tentree","outerknown","zipcar"],
    "Consumer Tech & Wearables":    ["wearable","smart ring","oura","whoop","levels health","withings","fitness tracker","strava","air platforms","hungryroot"],
    "Food Service & Hospitality":   ["restaurant","fast casual","food delivery","sweetgreen","shake shack","kopi kenangan","hospitality"],
    "Personal Care & Hygiene":      ["deodorant","toothpaste","shampoo","conditioner","body wash","oral care","dental","razor","native deodorant","by humankind","quip","cocofloss","soapbox","primally pure"],
}

def classify(name, description=""):
    text = (name + " " + description).lower()
    scores = {}
    for cat, kws in CATEGORY_MAP.items():
        score = sum(1 for kw in kws if kw in text)
        if score > 0:
            scores[cat] = score
    return max(scores, key=scores.get) if scores else "Food & Beverage"

# ── Jina fetcher ──────────────────────────────────────────────────────────────

def jina_fetch(url, timeout=30):
    try:
        r = requests.get(
            f"https://r.jina.ai/{url}",
            headers={"Accept": "text/plain", "User-Agent": "Prism/1.0"},
            timeout=timeout
        )
        if r.status_code == 200:
            return r.text
        print(f"  Jina HTTP {r.status_code} for {url}")
        return ""
    except Exception as e:
        print(f"  Jina error for {url}: {e}")
        return ""

# ── Per-fund parsers ──────────────────────────────────────────────────────────

def parse_lerer_hippeau(md):
    """
    Pattern: [Exited]\nCompanyName\nSectorLabel\nDescription\n
    """
    companies = []
    lines = [l.strip() for l in md.split('\n') if l.strip()]
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Detect "Exited" marker
        is_exited = False
        if line == "Exited":
            is_exited = True
            i += 1
            if i >= len(lines):
                break
            line = lines[i]
        
        # Skip image lines and nav items
        if line.startswith("!") or line.startswith("[") or line.startswith("#") or line.startswith("*"):
            i += 1
            continue
        
        # Company name: title case, 2-6 words, not a sector label
        words = line.split()
        SECTOR_LABELS = {"Commerce","FinTech","AI/ML","Healthcare","Wellness & Longevity","Food & Beverage",
                         "Beauty","Fashion","Consumer","Education","Supply Chain","Energy","Real Estate",
                         "Media","Retail","SaaS","Marketplace","Logistics","Energy Transition","Proptech",
                         "Robotics","Marketing Services"}
        
        if (1 <= len(words) <= 7 and 3 <= len(line) <= 60 
                and line[0].isupper() and line not in SECTOR_LABELS
                and not any(skip in line.lower() for skip in ["privacy","terms","copyright","©","contact","about","team"])):
            
            # Next line is likely the sector
            sector = lines[i+1] if i+1 < len(lines) else ""
            description = lines[i+2] if i+2 < len(lines) else ""
            
            # Validate: sector should be short or contain known sector words
            if len(sector.split()) <= 6:
                companies.append({
                    "company_name": line,
                    "description": description[:200] if not description.startswith("!") else "",
                    "status": "exited" if is_exited else "active",
                    "exit_type": None,
                    "data_source": "scraped",
                })
                i += 3
                continue
        
        i += 1
    
    return companies


def parse_heading_list(md, fund_name=""):
    """Generic parser: extract ### HeadingName patterns (common for Shopify/blog-style portfolio pages)"""
    companies = []
    
    # Pattern 1: ### Company Name repeated (Shopify blog)
    names = re.findall(r'^#{2,4}\s+([A-Z][^\n]{2,50})$', md, re.MULTILINE)
    seen = set()
    for name in names:
        name = name.strip()
        # Deduplicate (Shopify often repeats names)
        if name in seen:
            continue
        seen.add(name)
        
        # Skip nav/meta headings
        if any(skip in name.lower() for skip in ["connect","about","team","contact","invest","portfolio","mentor","resource","career"]):
            continue
        if len(name.split()) > 8 or len(name) < 3:
            continue
        
        companies.append({
            "company_name": name,
            "description": "",
            "status": "active",
            "exit_type": None,
            "data_source": "scraped",
        })
    
    # Pattern 2: bullet list items with company names
    if not companies:
        items = re.findall(r'^\*\s+\[?([A-Z][^\]\n]{2,40})\]?', md, re.MULTILINE)
        for name in items:
            name = name.strip()
            if len(name.split()) <= 6 and name not in seen:
                seen.add(name)
                companies.append({
                    "company_name": name,
                    "description": "",
                    "status": "active",
                    "exit_type": None,
                    "data_source": "scraped",
                })
    
    return companies


def parse_link_names(md):
    """Extract company names from markdown links: [CompanyName](url)"""
    companies = []
    seen = set()
    
    # Links: [Name](url) where url points to company site
    links = re.findall(r'\[([^\]]{3,50})\]\(https?://(?!(?:www\.)?(?:lererhippeau|forerunner|coefficient|imaginary|collaborative|selva|vmg|bfg|lcatterton|monogram|silas|circleup|willow|truebeauty))[^\)]+\)', md)
    for name in links:
        name = name.strip()
        if name in seen or not name[0].isupper():
            continue
        if any(skip in name.lower() for skip in ["about","contact","team","news","blog","home","press","jobs","careers","fund","login","sign","privacy","terms","learn","read","view","get","start","join","follow","watch"]):
            continue
        if len(name.split()) > 6 or len(name) < 3:
            continue
        seen.add(name)
        companies.append({
            "company_name": name,
            "description": "",
            "status": "active",
            "exit_type": None,
            "data_source": "scraped",
        })
    
    return companies


# ── Fund configs ──────────────────────────────────────────────────────────────

FUNDS = [
    {
        "name": "Lerer Hippeau",
        "url": "https://www.lererhippeau.com/portfolio",
        "parser": "lerer_hippeau",
    },
    {
        "name": "True Beauty Ventures",
        "url": "https://www.truebeautyventures.com/blogs/current-investments",
        "parser": "heading_list",
    },
    {
        "name": "Selva Ventures",
        "url": "https://www.selvaventures.com/portfolio",
        "parser": "link_names",
    },
    {
        "name": "Collaborative Fund",
        "url": "https://collabfund.com/portfolio/",
        "parser": "heading_list",
    },
    {
        "name": "BFG Partners",
        "url": "https://www.bfgpartners.com/portfolio",
        "parser": "link_names",
    },
    {
        "name": "VMG Catalyst",
        "url": "https://www.vmgpartners.com/companies/",
        "parser": "link_names",
    },
    {
        "name": "L Catterton",
        "url": "https://www.lcatterton.com/Investments.html",
        "parser": "link_names",
    },
]

# ── Supabase helpers ──────────────────────────────────────────────────────────

def get_existing():
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/landscape_deals?select=company_name,fund_name&limit=1000",
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    )
    return {(d["fund_name"], d["company_name"]) for d in resp.json()}


def insert_deals(deals):
    if not deals:
        return 0
    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/landscape_deals",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
        json=deals
    )
    return resp.status_code


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"\nPrism Portfolio Scraper (Jina) — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    existing = get_existing()
    print(f"Existing entries in DB: {len(existing)}\n")

    all_new = []

    for fund in FUNDS:
        print(f"→ {fund['name']}")
        md = jina_fetch(fund["url"])
        if not md:
            print(f"  No content — skipping")
            time.sleep(2)
            continue

        parser = fund["parser"]
        if parser == "lerer_hippeau":
            companies = parse_lerer_hippeau(md)
        elif parser == "heading_list":
            companies = parse_heading_list(md, fund["name"])
        elif parser == "link_names":
            companies = parse_link_names(md)
        else:
            companies = []

        print(f"  {len(companies)} companies extracted")

        for c in companies:
            key = (fund["name"], c["company_name"])
            if key in existing:
                continue

            record = {
                "fund_name": fund["name"],
                "company_name": c["company_name"],
                "category": classify(c["company_name"], c.get("description", "")),
                "round_stage": "Portfolio",
                "round_size_m": None,
                "deal_date": "2025-01-01",
                "status": c.get("status", "active"),
                "exit_type": c.get("exit_type"),
                "exit_acquirer": c.get("exit_acquirer"),
                "exit_date": c.get("exit_date"),
                "investment_date": c.get("investment_date"),
                "source_url": fund["url"],
                "description": c.get("description", "")[:300],
                "data_source": "scraped",
            }
            all_new.append(record)
            existing.add(key)

        time.sleep(2)  # polite delay between funds

    print(f"\nNew entries to insert: {len(all_new)}")

    if all_new:
        for i in range(0, len(all_new), 100):
            batch = all_new[i:i+100]
            status = insert_deals(batch)
            print(f"  Batch {i//100 + 1} ({len(batch)} records): HTTP {status}")

    # Final count
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/landscape_deals?select=id&limit=1",
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Prefer": "count=exact", "Range": "0-0"}
    )
    print(f"\nTotal in landscape_deals: {resp.headers.get('content-range', '?')}")
    print("Done.")


if __name__ == "__main__":
    main()
