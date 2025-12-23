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

MAX_CONCURRENT_BROWSERS = 3
sem = asyncio.Semaphore(MAX_CONCURRENT_BROWSERS)

async def run_scraper_safe(scraper_func, q):
    async with sem:
        try:
            return await scraper_func(q)
        except Exception as e:
            print(f"❌ Error in scraper: {e}")
            return []

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
        s = p['store']
        if s == 'Colruyt': p['logo'] = 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Colruyt-Logo-2023.svg/320px-Colruyt-Logo-2023.svg.png'
        elif s == 'Albert Heijn': p['logo'] = 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/Albert_Heijn_logo.svg/274px-Albert_Heijn_logo.svg.png'
        elif s == 'Aldi': p['logo'] = 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/Aldi_Nord_201x_logo.svg/256px-Aldi_Nord_201x_logo.svg.png'
        elif s == 'Delhaize': p['logo'] = 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Delhaize_Lion_Logo.svg/1024px-Delhaize_Lion_Logo.svg.png'
        elif s == 'Lidl': p['logo'] = 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Lidl-Logo.svg/1024px-Lidl-Logo.svg.png'
        elif s == 'Jumbo': p['logo'] = 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ee/Jumbo_Logo.svg/1200px-Jumbo_Logo.svg.png'
        elif s == 'Carrefour': p['logo'] = 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Carrefour_logo.svg/1024px-Carrefour_logo.svg.png'
        elif s == 'Prik&Tik': p['logo'] = 'https://www.prikentik.be/static/version1733984638/frontend/PrikEnTik/default/nl_BE/images/logo.svg'
        elif s == 'Snuffelstore': p['logo'] = 'https://www.snuffelstore.be/wp-content/uploads/2021/04/snuffelstore-logo-1.png'
        elif s == 'Drinks Corner': p['logo'] = 'https://drinkscorner.be/wp-content/uploads/2023/10/DrinksCorner-Logo-web-150x64.png'
    all_products = [p for p in all_products if p['price'] > 0]
    all_products.sort(key=lambda x: x['price_per_liter'] if x['price_per_liter'] > 0 else 999)
    return all_products
