"""
Portfolio scrapers for consumer incubators.

Approach per source:
  - Maesa       → HTML parse (static nav, reliable)
  - HumanCo     → HTML parse (static page, reliable)
  - Science Inc. → curated (JS-rendered, not scrapable)
  - Harry's Labs → curated (JS-rendered, not scrapable)
  - Beach House  → curated (site intermittently down)
  - Prehype      → curated (internal venture studio)
  - Unilever     → curated (too large, filter to relevant consumer brands)
  - SKS          → curated (JS-rendered)
  - Techstars    → curated (JS-rendered)
  - Target Acc.  → curated (JS-rendered)

All functions return a list of brand dicts compatible with consumer_founders schema.
Updated: March 2026.
"""

import re
import logging
import requests

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _get(url, timeout=10):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception as e:
        log.warning(f"Fetch failed for {url}: {e}")
        return ""


# ── HTML scrapers ──────────────────────────────────────────────

def scrape_maesa():
    """
    Maesa brand portfolio — parsed from /pages/* links in HTML nav.
    Live at: https://maesa.com
    Brands: Kristin Ess, Hairitage, Being Frenshe, Fine'ry, MIX:BAR, ITK, Koze Place, Niches & Nooks
    """
    BRAND_MAP = {
        "kristin-ess":   ("Kristin Ess Hair",  "haircare",       "celebrity haircare"),
        "hairitage":     ("Hairitage",          "beauty",         "mass haircare"),
        "being-frenshe": ("Being Frenshe",      "beauty",         "celebrity wellness beauty"),
        "finery":        ("Fine'ry",            "beauty",         "fragrance"),
        "mix-bar":       ("MIX:BAR",            "beauty",         "fragrance bar"),
        "itk":           ("ITK",                "beauty",         "Gen Z skincare"),
        "koze-place":    ("Koze Place",         "home & lifestyle","home fragrance"),
        "niches-nooks":  ("Niches & Nooks",     "beauty",         "intimate care"),
    }

    html = _get("https://maesa.com")
    found = set(re.findall(r"/pages/([\w-]+)", html))
    log.info(f"Maesa pages found in HTML: {found}")

    brands = []
    for slug, (name, cat, sub) in BRAND_MAP.items():
        if slug in found or not html:  # always include if scrape failed
            brands.append({
                "brand_name":   name,
                "category":     cat,
                "sub_category": sub,
                "accelerator":  "Maesa",
                "stage":        "seed",
                "source":       "Maesa",
                "source_url":   f"https://maesa.com/pages/{slug}",
            })

    # If HTML fetch failed, fall back to full curated list
    if not html:
        log.warning("Maesa HTML fetch failed — using full curated fallback")
        for slug, (name, cat, sub) in BRAND_MAP.items():
            if not any(b["brand_name"] == name for b in brands):
                brands.append({
                    "brand_name":   name,
                    "category":     cat,
                    "sub_category": sub,
                    "accelerator":  "Maesa",
                    "stage":        "seed",
                    "source":       "Maesa",
                    "source_url":   f"https://maesa.com/pages/{slug}",
                })

    log.info(f"Maesa: {len(brands)} brands")
    return brands


def scrape_humanco():
    """
    HumanCo brand portfolio — parsed from /our-brands HTML.
    Live at: https://www.humanco.com/our-brands
    Known: True Food Kitchen, Grove Collaborative, Against the Grain
    """
    BRAND_MAP = {
        "True Food Kitchen":  ("food & beverage", "wellness dining",    "series-a",  "https://www.truefoodkitchen.com"),
        "Grove Collaborative":("sustainability",   "eco household",      "public",    "https://www.grove.co"),
        "Against the Grain":  ("food & beverage", "gluten-free pasta",  "seed",      "https://www.againstthegrain.com"),
    }

    html = _get("https://www.humanco.com/our-brands")

    brands = []
    for name, (cat, sub, stage, url) in BRAND_MAP.items():
        if not html or name.lower() in html.lower():
            brands.append({
                "brand_name":   name,
                "category":     cat,
                "sub_category": sub,
                "accelerator":  "HumanCo",
                "stage":        stage,
                "source":       "HumanCo",
                "source_url":   url,
            })

    log.info(f"HumanCo: {len(brands)} brands")
    return brands


# ── Curated lists (JS-rendered or complex sites) ───────────────

def curated_science_inc():
    """
    Science Inc. portfolio — DTC-native brand builder.
    Site: https://science-inc.com (JS-rendered, not scrapable)
    Portfolio sourced from press coverage + Crunchbase.
    """
    return [
        {"brand_name": "MeUndies",        "category": "apparel",          "sub_category": "DTC underwear",        "stage": "series-a"},
        {"brand_name": "FabFitFun",       "category": "beauty",           "sub_category": "subscription box",     "stage": "series-a"},
        {"brand_name": "Hello Bello",     "category": "baby & kids",      "sub_category": "organic baby care",    "stage": "seed"},
        {"brand_name": "Habit",           "category": "food & beverage",  "sub_category": "personalized nutrition","stage": "acquired"},
        {"brand_name": "Pattern Brands",  "category": "home & lifestyle", "sub_category": "DTC home goods",       "stage": "series-a"},
        {"brand_name": "Dollar Shave Club","category": "personal care",   "sub_category": "men's grooming",       "stage": "acquired"},
        {"brand_name": "Liquid I.V.",     "category": "food & beverage",  "sub_category": "hydration multiplier", "stage": "acquired"},
    ]


def curated_harrys_labs():
    """
    Harry's Labs portfolio — DTC-native incubator arm of Harry's.
    Site: https://harrys.com/en/us/labs (JS-rendered)
    Portfolio sourced from press coverage.
    """
    return [
        {"brand_name": "Flamingo",        "category": "personal care",    "sub_category": "women's body care",    "stage": "series-a"},
        {"brand_name": "Cat Person",      "category": "pet",              "sub_category": "cat food & care",      "stage": "seed"},
        {"brand_name": "Headquarters",    "category": "personal care",    "sub_category": "men's haircare",       "stage": "seed"},
    ]


def curated_beach_house_group():
    """
    Beach House Group portfolio — celebrity-driven beauty brand builder.
    Site: https://beachhousegroup.com (intermittently unreachable)
    Portfolio sourced from press coverage.
    """
    return [
        {"brand_name": "Pattern Beauty",  "category": "beauty",           "sub_category": "textured haircare",    "stage": "series-a"},
        {"brand_name": "Cay Skin",        "category": "beauty",           "sub_category": "skin care SPF",        "stage": "seed"},
        {"brand_name": "LoveSeen",        "category": "beauty",           "sub_category": "lashes & eye",         "stage": "seed"},
        {"brand_name": "Ami Colé",        "category": "beauty",           "sub_category": "melanin-focused makeup","stage": "seed"},
    ]


def curated_prehype():
    """
    Prehype portfolio — venture studio, co-builds with founders.
    Site: https://prehype.com (static but no public portfolio page)
    Notable ventures sourced from press coverage.
    """
    return [
        {"brand_name": "Headspace",       "category": "health & wellness","sub_category": "mental wellness app",  "stage": "acquired"},
        {"brand_name": "Audos",           "category": "consumer tech",    "sub_category": "podcast tools",        "stage": "seed"},
        {"brand_name": "Freespin",        "category": "consumer tech",    "sub_category": "financial wellness",   "stage": "seed"},
    ]


def curated_unilever_foundry():
    """
    Unilever Foundry — corporate accelerator / incubation arm.
    Focuses on scaling & distribution. Consumer brands acquired or partnered.
    Portfolio sourced from Unilever IR + press.
    """
    return [
        {"brand_name": "Olly Nutrition",  "category": "health & wellness","sub_category": "gummy vitamins",       "stage": "acquired"},
        {"brand_name": "Graze",           "category": "food & beverage",  "sub_category": "healthy snacks",       "stage": "acquired"},
        {"brand_name": "REN Skincare",    "category": "beauty",           "sub_category": "clean skincare",       "stage": "acquired"},
        {"brand_name": "Tatcha",          "category": "beauty",           "sub_category": "Japanese-inspired skincare","stage": "acquired"},
        {"brand_name": "Love Beauty and Planet","category":"beauty",      "sub_category": "sustainable haircare",  "stage": "public"},
        {"brand_name": "Nutrafol",        "category": "health & wellness","sub_category": "hair growth supplements","stage": "acquired"},
    ]


def curated_sks_accelerator():
    """SKS Accelerator — sustainable consumer brands."""
    return [
        {"brand_name": "Loliware",        "category": "sustainability",   "sub_category": "compostable packaging","stage": "seed"},
        {"brand_name": "Foodshed",        "category": "food & beverage",  "sub_category": "local supply chain",   "stage": "pre-raise"},
        {"brand_name": "Bucha Brewers",   "category": "food & beverage",  "sub_category": "kombucha",             "stage": "seed"},
        {"brand_name": "Pela",            "category": "sustainability",   "sub_category": "compostable phone cases","stage": "series-a"},
        {"brand_name": "Open Water",      "category": "food & beverage",  "sub_category": "sustainable water",    "stage": "seed"},
        {"brand_name": "Imperfect Foods", "category": "food & beverage",  "sub_category": "reduced-waste grocery","stage": "series-b"},
    ]


def curated_techstars_consumer():
    """Techstars Consumer / Retail — general consumer accelerator."""
    return [
        {"brand_name": "Wandering Bear Coffee","category":"food & beverage","sub_category":"cold brew",           "stage": "seed"},
        {"brand_name": "Koia",            "category": "food & beverage",  "sub_category": "plant protein drink", "stage": "series-a"},
        {"brand_name": "Banza",           "category": "food & beverage",  "sub_category": "chickpea pasta",      "stage": "acquired"},
        {"brand_name": "Miku",            "category": "food & beverage",  "sub_category": "Japanese rice balls", "stage": "seed"},
        {"brand_name": "Supergut",        "category": "food & beverage",  "sub_category": "gut health snacks",   "stage": "seed"},
    ]


def curated_target_accelerator():
    """Target Accelerator — retail-focused consumer brands."""
    return [
        {"brand_name": "Live Más Skincare","category": "beauty",          "sub_category": "latina-founded",      "stage": "pre-raise"},
        {"brand_name": "Base Coat",        "category": "beauty",          "sub_category": "non-toxic nail care",  "stage": "seed"},
        {"brand_name": "Crown Affair",     "category": "beauty",          "sub_category": "ritual haircare",      "stage": "seed"},
        {"brand_name": "Golde",            "category": "health & wellness","sub_category": "superfood supplements","stage": "seed"},
        {"brand_name": "Prados Beauty",    "category": "beauty",          "sub_category": "indigenous-founded makeup","stage": "seed"},
        {"brand_name": "Hue",             "category": "beauty",           "sub_category": "shade-inclusive makeup","stage": "seed"},
    ]


# ── Aggregator ─────────────────────────────────────────────────

ACCELERATOR_SOURCE_URLS = {
    "Science Inc.":       "https://science-inc.com",
    "Harry's Labs":       "https://harrys.com/en/us/labs",
    "Maesa":              "https://maesa.com",
    "Beach House Group":  "https://beachhousegroup.com",
    "HumanCo":            "https://www.humanco.com",
    "Prehype":            "https://prehype.com",
    "Unilever Foundry":   "https://www.unilever.com/planet-and-society/unilever-foundry",
    "SKS Accelerator":    "https://sksaccelerator.com",
    "Techstars Consumer": "https://www.techstars.com/portfolio",
    "Target Accelerator": "https://corporate.target.com",
}


def scrape_all_portfolios():
    """
    Aggregate all incubator portfolios into a single list
    compatible with consumer_founders schema.
    """
    all_brands = []

    scrapers = [
        ("Maesa",              scrape_maesa),
        ("HumanCo",            scrape_humanco),
        ("Science Inc.",       lambda: curated_science_inc()),
        ("Harry's Labs",       lambda: curated_harrys_labs()),
        ("Beach House Group",  lambda: curated_beach_house_group()),
        ("Prehype",            lambda: curated_prehype()),
        ("Unilever Foundry",   lambda: curated_unilever_foundry()),
        ("SKS Accelerator",    lambda: curated_sks_accelerator()),
        ("Techstars Consumer", lambda: curated_techstars_consumer()),
        ("Target Accelerator", lambda: curated_target_accelerator()),
    ]

    for name, fn in scrapers:
        try:
            brands = fn()
            for b in brands:
                b.setdefault("accelerator", name)
                b.setdefault("source", name)
                b.setdefault("source_url", ACCELERATOR_SOURCE_URLS.get(name, ""))
                b.setdefault("cohort", "2026")
            all_brands.extend(brands)
            log.info(f"{name}: {len(brands)} brands loaded")
        except Exception as e:
            log.error(f"Portfolio scraper failed for {name}: {e}")

    log.info(f"Total portfolio brands: {len(all_brands)}")
    return all_brands
