"""
Portfolio scrapers for consumer incubators + VC funds.

Approach per source:
  - Maesa              → HTML parse (static nav, reliable)
  - HumanCo            → HTML parse (static page, reliable)
  - Forerunner         → HTML parse (server-side rendered h2 + category tags)
  - Science Inc.       → curated (JS-rendered, not scrapable)
  - Harry's Labs       → curated (JS-rendered, not scrapable)
  - Beach House        → curated (site intermittently down)
  - Prehype            → curated (internal venture studio)
  - Unilever           → curated (too large, filter to relevant consumer brands)
  - SKS                → curated (JS-rendered)
  - Techstars          → curated (JS-rendered)
  - Target Acc.        → curated (JS-rendered)
  - Imaginary Ventures → curated (JS-rendered, Natalie Massenet's consumer fund)
  - Coefficient Capital→ curated (JS-rendered, CPG consumer specialists)
  - VMG Partners       → curated (JS-rendered, authentic consumer brand growth equity)

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
        {"brand_name": "MeUndies",         "category": "apparel",          "sub_category": "DTC underwear",         "stage": "series-a",  "source_url": "https://www.meundies.com"},
        {"brand_name": "FabFitFun",        "category": "beauty",           "sub_category": "subscription box",      "stage": "series-a",  "source_url": "https://fabfitfun.com"},
        {"brand_name": "Hello Bello",      "category": "baby & kids",      "sub_category": "organic baby care",     "stage": "seed",      "source_url": "https://hellobello.com"},
        {"brand_name": "Habit",            "category": "food & beverage",  "sub_category": "personalized nutrition","stage": "acquired",  "source_url": "https://habit.com"},
        {"brand_name": "Pattern Brands",   "category": "home & lifestyle", "sub_category": "DTC home goods",        "stage": "series-a",  "source_url": "https://patternbrands.com"},
        {"brand_name": "Dollar Shave Club","category": "personal care",    "sub_category": "men's grooming",        "stage": "acquired",  "source_url": "https://www.dollarshaveclub.com"},
        {"brand_name": "Liquid I.V.",      "category": "food & beverage",  "sub_category": "hydration multiplier",  "stage": "acquired",  "source_url": "https://www.liquid-iv.com"},
    ]


def curated_harrys_labs():
    """
    Harry's Labs portfolio — DTC-native incubator arm of Harry's.
    Site: https://harrys.com/en/us/labs (JS-rendered)
    Portfolio sourced from press coverage.
    """
    return [
        {"brand_name": "Flamingo",         "category": "personal care",    "sub_category": "women's body care",     "stage": "series-a",  "source_url": "https://www.shopflamingo.com"},
        {"brand_name": "Cat Person",       "category": "pet",              "sub_category": "cat food & care",       "stage": "seed",      "source_url": "https://www.catperson.com"},
        {"brand_name": "Headquarters",     "category": "personal care",    "sub_category": "men's haircare",        "stage": "seed",      "source_url": "https://www.hqhair.com"},
    ]


def curated_beach_house_group():
    """
    Beach House Group portfolio — celebrity-driven beauty brand builder.
    Site: https://beachhousegroup.com (intermittently unreachable)
    Portfolio sourced from press coverage.
    """
    return [
        {"brand_name": "Pattern Beauty",   "category": "beauty",           "sub_category": "textured haircare",     "stage": "series-a",  "source_url": "https://www.patternbeauty.com"},
        {"brand_name": "Cay Skin",         "category": "beauty",           "sub_category": "skin care SPF",         "stage": "seed",      "source_url": "https://www.cayskin.com"},
        {"brand_name": "LoveSeen",         "category": "beauty",           "sub_category": "lashes & eye",          "stage": "seed",      "source_url": "https://loveseen.com"},
        {"brand_name": "Ami Colé",         "category": "beauty",           "sub_category": "melanin-focused makeup","stage": "seed",      "source_url": "https://www.amicole.com"},
    ]


def curated_prehype():
    """
    Prehype portfolio — venture studio, co-builds with founders.
    Site: https://prehype.com (static but no public portfolio page)
    Notable ventures sourced from press coverage.
    """
    return [
        {"brand_name": "Headspace",        "category": "health & wellness","sub_category": "mental wellness app",   "stage": "acquired",  "source_url": "https://www.headspace.com"},
        {"brand_name": "Audos",            "category": "consumer tech",    "sub_category": "podcast tools",         "stage": "seed",      "source_url": "https://www.audos.com"},
        {"brand_name": "Freespin",         "category": "consumer tech",    "sub_category": "financial wellness",    "stage": "seed",      "source_url": "https://prehype.com"},
    ]


def curated_unilever_foundry():
    """
    Unilever Foundry — corporate accelerator / incubation arm.
    Focuses on scaling & distribution. Consumer brands acquired or partnered.
    Portfolio sourced from Unilever IR + press.
    """
    return [
        {"brand_name": "Olly Nutrition",        "category": "health & wellness","sub_category": "gummy vitamins",            "stage": "acquired", "source_url": "https://www.olly.com"},
        {"brand_name": "Graze",                 "category": "food & beverage",  "sub_category": "healthy snacks",            "stage": "acquired", "source_url": "https://www.graze.com"},
        {"brand_name": "REN Skincare",          "category": "beauty",           "sub_category": "clean skincare",            "stage": "acquired", "source_url": "https://www.renskincare.com"},
        {"brand_name": "Tatcha",                "category": "beauty",           "sub_category": "Japanese-inspired skincare","stage": "acquired", "source_url": "https://www.tatcha.com"},
        {"brand_name": "Love Beauty and Planet","category": "beauty",           "sub_category": "sustainable haircare",      "stage": "public",   "source_url": "https://www.lovebeautyandplanet.com"},
        {"brand_name": "Nutrafol",              "category": "health & wellness","sub_category": "hair growth supplements",   "stage": "acquired", "source_url": "https://nutrafol.com"},
    ]


def curated_sks_accelerator():
    """SKS Accelerator — sustainable consumer brands."""
    return [
        {"brand_name": "Loliware",         "category": "sustainability",   "sub_category": "compostable packaging", "stage": "seed",      "source_url": "https://loliware.com"},
        {"brand_name": "Foodshed",         "category": "food & beverage",  "sub_category": "local supply chain",    "stage": "pre-raise", "source_url": "https://foodshed.com"},
        {"brand_name": "Bucha Brewers",    "category": "food & beverage",  "sub_category": "kombucha",              "stage": "seed",      "source_url": "https://buchabrewing.com"},
        {"brand_name": "Pela",             "category": "sustainability",   "sub_category": "compostable phone cases","stage": "series-a",  "source_url": "https://pela.earth"},
        {"brand_name": "Open Water",       "category": "food & beverage",  "sub_category": "sustainable water",     "stage": "seed",      "source_url": "https://www.drinkOpenWater.com"},
        {"brand_name": "Imperfect Foods",  "category": "food & beverage",  "sub_category": "reduced-waste grocery", "stage": "series-b",  "source_url": "https://www.imperfectfoods.com"},
    ]


def curated_techstars_consumer():
    """Techstars Consumer / Retail — general consumer accelerator."""
    return [
        {"brand_name": "Wandering Bear Coffee","category": "food & beverage","sub_category": "cold brew",           "stage": "seed",      "source_url": "https://wanderingbearcoffee.com"},
        {"brand_name": "Koia",             "category": "food & beverage",  "sub_category": "plant protein drink",  "stage": "series-a",  "source_url": "https://drinkkoia.com"},
        {"brand_name": "Banza",            "category": "food & beverage",  "sub_category": "chickpea pasta",       "stage": "acquired",  "source_url": "https://eatbanza.com"},
        {"brand_name": "Supergut",         "category": "food & beverage",  "sub_category": "gut health snacks",    "stage": "seed",      "source_url": "https://www.supergut.com"},
        {"brand_name": "Oat Haus",         "category": "food & beverage",  "sub_category": "granola butter",       "stage": "seed",      "source_url": "https://oathaus.com"},
    ]


def curated_target_accelerator():
    """Target Accelerator — retail-focused consumer brands."""
    return [
        {"brand_name": "Live Más Skincare","category": "beauty",           "sub_category": "latina-founded",        "stage": "pre-raise", "source_url": "https://livemasskincare.com"},
        {"brand_name": "Base Coat",        "category": "beauty",           "sub_category": "non-toxic nail care",   "stage": "seed",      "source_url": "https://www.basecoatbeauty.com"},
        {"brand_name": "Crown Affair",     "category": "beauty",           "sub_category": "ritual haircare",       "stage": "seed",      "source_url": "https://www.crownaffair.com"},
        {"brand_name": "Golde",            "category": "health & wellness","sub_category": "superfood supplements", "stage": "seed",      "source_url": "https://golde.co"},
        {"brand_name": "Prados Beauty",    "category": "beauty",           "sub_category": "indigenous-founded makeup","stage": "seed",   "source_url": "https://pradosbeauty.com"},
        {"brand_name": "Hue",              "category": "beauty",           "sub_category": "shade-inclusive makeup","stage": "seed",      "source_url": "https://huebeauty.com"},
    ]


# ── Aggregator ─────────────────────────────────────────────────

# ── VC Fund scrapers ──────────────────────────────────────────

def scrape_forerunner():
    """
    Forerunner Ventures — live scrape of Brands & Experiences portfolio.
    Server-side rendered; company names in <h2> tags with category spans.
    URL: https://www.forerunnerventures.com/investments
    """
    html = _get("https://www.forerunnerventures.com/investments", timeout=12)
    if not html:
        return []

    # Each investment is an <h2> block followed by category + URL
    blocks = re.findall(r'<h2[^>]*>(.+?)</h2>(.*?)(?=<h2|$)', html, re.DOTALL)
    brands = []
    for name_raw, rest in blocks:
        name = re.sub(r'<[^>]+>', '', name_raw).strip()
        name = name.replace('&amp;', '&').replace('&#x27;', "'")
        if not name:
            continue
        # Only consumer-facing portfolio companies
        cat_m = re.search(r'<span[^>]*text-lavender[^>]*>([^<]+)</span>', rest)
        category_tag = cat_m.group(1).strip() if cat_m else ''
        if 'Brands' not in category_tag and 'Experiences' not in category_tag:
            continue
        # URL
        url_m = re.search(r'href=["\']([^"\']+)["\'][^>]*>Visit', rest)
        url = url_m.group(1).strip() if url_m else ''
        # Year
        yr_m = re.search(r'font-mono[^>]*>(\d{4}|Pre-\d{4})', rest)
        year = yr_m.group(1) if yr_m else ''
        brands.append({
            "brand_name":   name,
            "category":     _forerunner_category(name),
            "sub_category": _forerunner_sub(name),
            "stage":        "series-a",
            "source_url":   url,
            "cohort":       year or "2026",
        })
    log.info(f"Forerunner live scrape: {len(brands)} consumer brands")
    return brands


def _forerunner_category(name):
    HEALTH = {"Curology", "Headway", "Hims & Hers Health", "Joy", "Fay", "Oura",
              "Prenuvo", "Ritual", "Teal Health", "Superpower", "Dutch"}
    PET   = {"The Farmer's Dog", "Dutch"}
    HOME  = {"Homebound", "Wonder"}
    FOOD  = {"The Feed", "Magna"}
    KIDS  = {"KiwiCo"}
    FIN   = {"Chime", "Arrived Homes", "Atticus", "Basic Capital", "Zola"}
    BEAUTY = {"Glossier", "Prose", "Dollar Shave Club"}
    if name in HEALTH:  return "health tech"
    if name in PET:     return "pet"
    if name in HOME:    return "home & lifestyle"
    if name in FOOD:    return "food & beverage"
    if name in KIDS:    return "education"
    if name in FIN:     return "fintech"
    if name in BEAUTY:  return "beauty"
    return "consumer tech"


def _forerunner_sub(name):
    SUBS = {
        "Glossier":           "direct-to-consumer beauty",
        "Prose":              "personalized haircare",
        "Dollar Shave Club":  "subscription grooming",
        "Curology":           "personalized skincare",
        "Oura":               "health wearable",
        "Ritual":             "supplements",
        "Headway":            "mental health access",
        "Hims & Hers Health": "telehealth",
        "Prenuvo":            "preventive health imaging",
        "Teal Health":        "women's health",
        "Superpower":         "primary care",
        "Fay":                "nutrition coaching",
        "The Farmer's Dog":   "fresh pet food",
        "Dutch":              "virtual vet",
        "Away":               "direct-to-consumer travel",
        "Warby Parker":       "direct-to-consumer eyewear",
        "Cotopaxi":           "outdoor gear",
        "KiwiCo":             "kids STEM kits",
        "Chime":              "neobank",
        "Zola":               "wedding marketplace",
        "Wonder":             "food delivery",
        "Magna":              "functional beverages",
        "The Feed":           "performance nutrition",
        "Joy":                "parenting platform",
        "Homebound":          "custom homebuilding",
    }
    return SUBS.get(name, "consumer brand")


def curated_imaginary_ventures():
    """
    Imaginary Ventures — Natalie Massenet & Nick Brown.
    Premium direct-to-consumer brands across fashion, beauty, home.
    Curated: JS-rendered site.
    """
    return [
        {"brand_name": "Mejuri",         "category": "jewelry & accessories", "sub_category": "fine jewelry DTC",       "stage": "series-a", "source_url": "https://mejuri.com"},
        {"brand_name": "Cuyana",         "category": "fashion",               "sub_category": "essentials fashion DTC",  "stage": "series-a", "source_url": "https://cuyana.com"},
        {"brand_name": "Italic",         "category": "fashion",               "sub_category": "members-only DTC marketplace","stage": "seed",  "source_url": "https://italic.com"},
        {"brand_name": "Jolie",          "category": "beauty",                "sub_category": "skin-first shower filters", "stage": "seed",   "source_url": "https://jolieskinco.com"},
        {"brand_name": "Caraway",        "category": "home & lifestyle",      "sub_category": "non-toxic cookware DTC",  "stage": "series-a", "source_url": "https://carawayhome.com"},
        {"brand_name": "Summer Fridays", "category": "beauty",                "sub_category": "clean skincare",          "stage": "series-a", "source_url": "https://summerfridays.com"},
        {"brand_name": "Nécessaire",     "category": "beauty",                "sub_category": "body care essentials",    "stage": "series-a", "source_url": "https://necessaire.com"},
        {"brand_name": "Parachute Home", "category": "home & lifestyle",      "sub_category": "premium bedding DTC",     "stage": "series-a", "source_url": "https://parachutehome.com"},
        {"brand_name": "Pattern Brands", "category": "home & lifestyle",      "sub_category": "multi-brand home goods",  "stage": "series-a", "source_url": "https://pattern.com"},
        {"brand_name": "Ganni",          "category": "fashion",               "sub_category": "Scandi sustainable fashion","stage": "series-b","source_url": "https://ganni.com"},
        {"brand_name": "Vuori",          "category": "fashion",               "sub_category": "premium activewear",      "stage": "series-b", "source_url": "https://vuoriclothing.com"},
        {"brand_name": "Allbirds",       "category": "fashion",               "sub_category": "sustainable footwear DTC","stage": "public",   "source_url": "https://allbirds.com"},
    ]


def curated_coefficient_capital():
    """
    Coefficient Capital — Taylor Black & Matthew Weiss.
    CPG consumer specialists: food, beverage, beauty.
    Curated: JS-rendered site.
    """
    return [
        {"brand_name": "Olipop",        "category": "food & beverage",  "sub_category": "better-for-you soda",        "stage": "series-a", "source_url": "https://drinkolipop.com"},
        {"brand_name": "Fishwife",      "category": "food & beverage",  "sub_category": "premium tinned seafood",     "stage": "seed",     "source_url": "https://fishwife.co"},
        {"brand_name": "Graza",         "category": "food & beverage",  "sub_category": "squeeze-bottle olive oil",   "stage": "seed",     "source_url": "https://graza.co"},
        {"brand_name": "Brightland",    "category": "food & beverage",  "sub_category": "premium California olive oil","stage": "seed",    "source_url": "https://brightland.co"},
        {"brand_name": "Fly by Jing",   "category": "food & beverage",  "sub_category": "Sichuan condiments DTC",     "stage": "seed",     "source_url": "https://flybyjing.com"},
        {"brand_name": "Magic Spoon",   "category": "food & beverage",  "sub_category": "high-protein cereal",        "stage": "series-a", "source_url": "https://magicspoon.com"},
        {"brand_name": "Ghia",          "category": "food & beverage",  "sub_category": "non-alcoholic apéritif",     "stage": "seed",     "source_url": "https://drinkghia.com"},
        {"brand_name": "Chomps",        "category": "food & beverage",  "sub_category": "grass-fed meat sticks",      "stage": "series-a", "source_url": "https://chomps.com"},
        {"brand_name": "Vacation",      "category": "beauty",           "sub_category": "retro sunscreen branding",   "stage": "seed",     "source_url": "https://yourvacation.life"},
        {"brand_name": "Recess",        "category": "food & beverage",  "sub_category": "adaptogen sparkling water",  "stage": "series-a", "source_url": "https://takearecess.com"},
        {"brand_name": "Acid League",   "category": "food & beverage",  "sub_category": "living vinegars + pantry",   "stage": "seed",     "source_url": "https://acidleague.com"},
        {"brand_name": "Brez",          "category": "food & beverage",  "sub_category": "THC/CBD micro-dose beverage","stage": "seed",     "source_url": "https://enjoybrez.com"},
    ]


def curated_vmg_partners():
    """
    VMG Partners — authentic consumer brand growth equity.
    Focus: Food & Beverage, Beauty, Wellness. Often growth/buyout stage.
    Curated: JS-rendered site.
    """
    return [
        {"brand_name": "Olaplex",          "category": "beauty",           "sub_category": "bond-building haircare",        "stage": "public",   "source_url": "https://olaplex.com"},
        {"brand_name": "COSRX",            "category": "beauty",           "sub_category": "K-beauty skincare",             "stage": "acquired", "source_url": "https://cosrx.com"},
        {"brand_name": "Farmhouse Culture","category": "food & beverage",  "sub_category": "probiotic kraut & gut shots",   "stage": "series-a", "source_url": "https://farmhouseculture.com"},
        {"brand_name": "Chosen Foods",     "category": "food & beverage",  "sub_category": "avocado oil kitchen staples",   "stage": "series-a", "source_url": "https://chosenfoods.com"},
        {"brand_name": "Pete & Gerry's",   "category": "food & beverage",  "sub_category": "organic free-range eggs",       "stage": "series-a", "source_url": "https://peteandgerrys.com"},
        {"brand_name": "MegaFood",         "category": "health tech",      "sub_category": "whole-food vitamins",           "stage": "series-a", "source_url": "https://megafood.com"},
        {"brand_name": "Caliwater",        "category": "food & beverage",  "sub_category": "cactus water functional bev",   "stage": "seed",     "source_url": "https://caliwater.com"},
        {"brand_name": "Bev",              "category": "food & beverage",  "sub_category": "female-founded canned wine",    "stage": "seed",     "source_url": "https://drinkbev.com"},
        {"brand_name": "Bondi Sands",      "category": "beauty",           "sub_category": "self-tan & suncare",            "stage": "series-a", "source_url": "https://bondisands.com"},
        {"brand_name": "Drunk Elephant",   "category": "beauty",           "sub_category": "clean clinical skincare",       "stage": "acquired", "source_url": "https://drunkelephant.com"},
        {"brand_name": "Native",           "category": "beauty",           "sub_category": "natural deodorant",             "stage": "acquired", "source_url": "https://nativecos.com"},
        {"brand_name": "Olly",             "category": "health tech",      "sub_category": "gummy supplements",             "stage": "acquired", "source_url": "https://olly.com"},
    ]


ACCELERATOR_SOURCE_URLS = {
    "Science Inc.":          "https://science-inc.com",
    "Harry's Labs":          "https://harrys.com/en/us/labs",
    "Maesa":                 "https://maesa.com",
    "Beach House Group":     "https://beachhousegroup.com",
    "HumanCo":               "https://www.humanco.com",
    "Prehype":               "https://prehype.com",
    "Unilever Foundry":      "https://www.unilever.com/planet-and-society/unilever-foundry",
    "SKS Accelerator":       "https://sksaccelerator.com",
    "Techstars Consumer":    "https://www.techstars.com/portfolio",
    "Target Accelerator":    "https://corporate.target.com",
    "Forerunner":            "https://www.forerunnerventures.com/investments",
    "Imaginary Ventures":    "https://imaginaryfuture.com",
    "Coefficient Capital":   "https://www.coefficientcapital.com/portfolio",
    "VMG Partners":          "https://www.vmgpartners.com/companies",
}


def scrape_all_portfolios():
    """
    Aggregate all incubator portfolios into a single list
    compatible with consumer_founders schema.
    """
    all_brands = []

    scrapers = [
        ("Maesa",                scrape_maesa),
        ("HumanCo",              scrape_humanco),
        ("Forerunner",           scrape_forerunner),
        ("Science Inc.",         lambda: curated_science_inc()),
        ("Harry's Labs",         lambda: curated_harrys_labs()),
        ("Beach House Group",    lambda: curated_beach_house_group()),
        ("Prehype",              lambda: curated_prehype()),
        ("Unilever Foundry",     lambda: curated_unilever_foundry()),
        ("SKS Accelerator",      lambda: curated_sks_accelerator()),
        ("Techstars Consumer",   lambda: curated_techstars_consumer()),
        ("Target Accelerator",   lambda: curated_target_accelerator()),
        ("Imaginary Ventures",   lambda: curated_imaginary_ventures()),
        ("Coefficient Capital",  lambda: curated_coefficient_capital()),
        ("VMG Partners",         lambda: curated_vmg_partners()),
    ]

    for name, fn in scrapers:
        try:
            brands = fn()
            for b in brands:
                b.setdefault("accelerator", name)
                b.setdefault("source", name)
                # Only fall back to incubator URL if no brand-level URL was set
                if not b.get("source_url"):
                    b["source_url"] = ACCELERATOR_SOURCE_URLS.get(name, "")
                b.setdefault("cohort", "2026")
            all_brands.extend(brands)
            log.info(f"{name}: {len(brands)} brands loaded")
        except Exception as e:
            log.error(f"Portfolio scraper failed for {name}: {e}")

    log.info(f"Total portfolio brands: {len(all_brands)}")
    return all_brands
