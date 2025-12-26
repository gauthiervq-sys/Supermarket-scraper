from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from app.utils import calculate_price_per_liter, parse_volume_from_text

from app.scrapers.colruyt import scrape_colruyt
from app.scrapers.ah import scrape_ah
from app.scrapers.aldi import scrape_aldi
from app.scrapers.delhaize import scrape_delhaize
from app.scrapers.lidl import scrape_lidl
from app.scrapers.jumbo import scrape_jumbo
from app.scrapers.carrefour import scrape_carrefour
from app.scrapers.prikentik import scrape_prikentik
from app.scrapers.small_shops import scrape_snuffelstore, scrape_drinkscorner

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Increase concurrency for faster scraping
MAX_CONCURRENT_BROWSERS = 5
sem = asyncio.Semaphore(MAX_CONCURRENT_BROWSERS)

async def run_scraper_safe(scraper_func, q):
    async with sem:
        try:
            # Add overall timeout per scraper to prevent hanging
            return await asyncio.wait_for(scraper_func(q), timeout=15.0)
        except asyncio.TimeoutError:
            print(f"⏱️ Timeout in scraper: {scraper_func.__name__}")
            return []
        except Exception as e:
            print(f"❌ Error in scraper {scraper_func.__name__}: {e}")
            return []

# Store logos using more reliable CDN sources
STORE_LOGOS = {
    'Colruyt': 'https://cdn.cookielaw.org/logos/01b5df24-cb0b-44a1-90e6-afd3f2e7bea0/36dcc7e0-97a6-422b-b3ad-c90e49082efd/91f51b8c-c0a7-4849-8b20-86e0fc38eeb7/Colruyt_Group_logo.png',
    'Albert Heijn': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/Albert_Heijn_logo.svg/274px-Albert_Heijn_logo.svg.png',
    'Aldi': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/Aldi_Nord_201x_logo.svg/256px-Aldi_Nord_201x_logo.svg.png',
    'Delhaize': 'https://static.delhaize.be/logo_delhaize.svg',
    'Lidl': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Lidl-Logo.svg/1024px-Lidl-Logo.svg.png',
    'Jumbo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ee/Jumbo_Logo.svg/1200px-Jumbo_Logo.svg.png',
    'Carrefour': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Carrefour_logo.svg/1024px-Carrefour_logo.svg.png',
    'Prik&Tik': 'https://www.prikentik.be/static/version1733984638/frontend/PrikEnTik/default/nl_BE/images/logo.svg',
    'Snuffelstore': 'https://www.snuffelstore.be/wp-content/uploads/2021/04/snuffelstore-logo-1.png',
    'Drinks Corner': 'https://drinkscorner.be/wp-content/uploads/2023/10/DrinksCorner-Logo-web-150x64.png'
}

@app.get("/search")
async def search_products(q: str = Query(..., min_length=2)):
    print(f"--- 🚦 Start Veilige Zoekopdracht: {q} ---")
    scrapers = [
        scrape_colruyt, scrape_ah, scrape_aldi, 
        scrape_delhaize, scrape_lidl, scrape_jumbo, 
        scrape_carrefour, scrape_prikentik, 
        scrape_snuffelstore, scrape_drinkscorner
    ]
    tasks = [run_scraper_safe(s, q) for s in scrapers]
    results = await asyncio.gather(*tasks)
    all_products = []
    for res in results:
        if res and isinstance(res, list):
            all_products.extend(res)
    for p in all_products:
        p['price_per_liter'] = calculate_price_per_liter(p['price'], p['volume'], p['name'])
        p['liter_value'] = parse_volume_from_text(p['volume']) 
        if p['liter_value'] == 0:
             p['liter_value'] = parse_volume_from_text(p['name'])
        if not p['volume']:
            if p['liter_value'] < 1: p['volume'] = f"{int(p['liter_value']*100)}cl"
            else: p['volume'] = f"{p['liter_value']}L"
        # Assign logo from the centralized dictionary
        p['logo'] = STORE_LOGOS.get(p['store'], '')
    all_products = [p for p in all_products if p['price'] > 0]
    all_products.sort(key=lambda x: x['price_per_liter'] if x['price_per_liter'] > 0 else 999)
    print(f"✅ Found {len(all_products)} products")
    return all_products
