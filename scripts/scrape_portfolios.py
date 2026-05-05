#!/usr/bin/env python3
"""
Prism — Fund Portfolio Scraper
Scrapes 14 consumer fund portfolio pages, classifies each company via Gemini,
and inserts into Supabase landscape_deals table.
"""

import os, json, time, requests
from datetime import datetime

GEMINI_KEY = "AIzaSyAlsqt4U2oBt4qITuxD4utwm4zqu8S6y0g"
SUPABASE_URL = "https://datqjbnetudvqjsxjczl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRhdHFqYm5ldHVkdnFqc3hqY3psIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE5NjMxMTIsImV4cCI6MjA4NzUzOTExMn0.8QY1ew74ahBLmhU5vAyZF-ygRGr0p4xpM8i0OLTV4-4"

CATEGORIES = [
    "Food & Beverage",
    "Functional Food & Bev",
    "Beauty & Skincare",
    "Wellness & Supplements",
    "Fitness & Sports",
    "Mental Health & Wellness Tech",
    "Fashion & Apparel",
    "Pet",
    "Home & Living",
    "Baby & Family",
    "Personal Care & Hygiene",
    "Consumer Health & Telehealth",
    "Sustainability & Eco",
    "Consumer Tech & Wearables",
    "Food Service & Hospitality",
]

FUNDS = [
    {"name": "Forerunner Ventures", "url": "https://forerunner.vc/portfolio"},
    {"name": "Imaginary Ventures", "url": "https://imaginary.vc"},
    {"name": "Coefficient Capital", "url": "https://www.coefficientcapital.com/portfolio"},
    {"name": "Collaborative Fund", "url": "https://www.collaborativefund.com/portfolio"},
    {"name": "True Beauty Ventures", "url": "https://www.truebeautyventures.com/portfolio"},
    {"name": "L Catterton", "url": "https://www.lcatterton.com/Portfolio.html"},
    {"name": "Lerer Hippeau", "url": "https://www.lererhippeau.com/portfolio"},
    {"name": "Selva Ventures", "url": "https://www.selvaventures.com/portfolio"},
    {"name": "Silas Capital", "url": "https://www.silascapital.com/portfolio"},
    {"name": "CircleUp", "url": "https://circleup.com/portfolio"},
    {"name": "BFG Partners", "url": "https://www.bfgpartners.com/portfolio"},
    {"name": "VMG Catalyst", "url": "https://www.vmgpartners.com/portfolio"},
    {"name": "Monogram Capital", "url": "https://monogramcapital.co/portfolio"},
    {"name": "Willow Growth", "url": "https://willowgrowthpartners.com/portfolio"},
]

def gemini(prompt):
    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}",
        headers={"Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=30
    )
    d = resp.json()
    if "error" in d:
        raise Exception(d["error"]["message"])
    return d["candidates"][0]["content"]["parts"][0]["text"].strip()

def fetch_page(url):
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        return r.text[:8000]  # limit to avoid token overflow
    except Exception as e:
        return f"ERROR fetching {url}: {e}"

def extract_companies(fund_name, html):
    prompt = f"""You are analyzing the portfolio page of {fund_name}, a consumer-focused VC fund.

Here is the page content (may be HTML or text):
---
{html[:6000]}
---

Extract all portfolio company names you can find. Return ONLY a JSON array of strings, nothing else.
Example: ["Company A", "Company B", "Company C"]
If you cannot find any companies, return: []"""
    
    result = gemini(prompt)
    # Clean up markdown if present
    result = result.strip().strip("```json").strip("```").strip()
    try:
        return json.loads(result)
    except:
        return []

def classify_company(company_name, fund_name):
    cats = "\n".join(f"- {c}" for c in CATEGORIES)
    prompt = f"""You are classifying consumer brands for a consumer VC intelligence tool.

The company "{company_name}" is a portfolio company of {fund_name}.

First, determine: is this a CONSUMER brand (sells products/services to end consumers, D2C, CPG, retail, wellness, beauty, food, fashion, etc.)?

If it is B2B software, developer tools, enterprise SaaS, payments infrastructure, or a wholesale/B2B platform — return exactly: SKIP

If it IS a consumer brand, classify it into exactly ONE of these categories:
{cats}

Return ONLY the category name exactly as written above, or SKIP. Nothing else."""
    
    try:
        result = gemini(prompt)
        result = result.strip()
        # Skip B2B companies
        if result.upper() == "SKIP" or "SKIP" in result.upper()[:10]:
            return None
        # Find best match
        for cat in CATEGORIES:
            if cat.lower() in result.lower():
                return cat
        return None  # unknown — skip rather than misclassify
    except Exception as e:
        print(f"  classify error for {company_name}: {e}")
        return None

def insert_deals(deals):
    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/landscape_deals",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        },
        json=deals
    )
    return resp.status_code

def main():
    print(f"Starting portfolio scrape — {datetime.now().isoformat()}\n")
    
    all_deals = []
    
    for fund in FUNDS:
        print(f"→ {fund['name']}")
        
        # Fetch portfolio page
        html = fetch_page(fund["url"])
        if html.startswith("ERROR"):
            print(f"  {html}")
            continue
        
        # Extract company names
        try:
            companies = extract_companies(fund["name"], html)
            print(f"  Found {len(companies)} companies: {companies[:5]}{'...' if len(companies)>5 else ''}")
        except Exception as e:
            print(f"  extract error: {e}")
            time.sleep(5)
            continue
        
        # Classify each company
        for company in companies[:30]:  # cap at 30 per fund
            time.sleep(1.5)  # rate limit: ~40 req/min on free tier
            try:
                category = classify_company(company, fund["name"])
                if category is None:
                    print(f"  ⊘ {company} → skipped (B2B or unclassifiable)")
                    continue
                deal = {
                    "fund_name": fund["name"],
                    "company_name": company,
                    "category": category,
                    "round_stage": "Portfolio",
                    "round_size_m": None,
                    "deal_date": "2025-01-01"  # approximate — historical
                }
                all_deals.append(deal)
                print(f"  ✓ {company} → {category}")
            except Exception as e:
                print(f"  ✗ {company}: {e}")
                if "quota" in str(e).lower():
                    print("  Quota hit — waiting 60s")
                    time.sleep(60)
        
        # Insert batch after each fund
        if all_deals:
            status = insert_deals(all_deals)
            print(f"  Inserted {len(all_deals)} deals → HTTP {status}")
            all_deals = []
        
        time.sleep(3)  # pause between funds
    
    print(f"\nDone — {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()
