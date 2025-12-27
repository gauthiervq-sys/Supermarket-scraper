import httpx
import urllib.parse
import logging
import os

DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
logger = logging.getLogger(__name__)

async def scrape_jumbo(search_term: str):
    results = []
    headers = {"User-Agent": "Jumbo/7.5.0 (Android)", "x-jumbo-unique-id": "android-device-123"}
    url = "https://mobileapi.jumbo.com/v17/search"
    params = {"q": search_term, "offset": 0, "limit": 15}
    
    logger.info(f"🐘 Jumbo: Checking API {url}?q={search_term}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers, params=params)
            if DEBUG_MODE:
                logger.debug(f"  Jumbo: API response status: {resp.status_code}")
            data = resp.json()
            items = data.get('products', {}).get('data', [])
            if DEBUG_MODE:
                logger.debug(f"  Jumbo: Found {len(items)} products in API response")
            for p in items:
                price_cent = p.get('prices', {}).get('price', {}).get('amount', 0)
                price = price_cent / 100 if price_cent else 0.0
                imgs = p.get('imageInfo', {}).get('primaryView', [])
                img = imgs[0].get('url', '') if imgs else ""
                # Ensure image URL is complete
                if img and not img.startswith('http'):
                    img = f"https:{img}" if img.startswith('//') else f"https://www.jumbo.com{img}"
                prod_id = p.get('id', '')
                title_slug = p.get('title', '').replace(' ', '-')
                link = f"https://www.jumbo.com/producten/{title_slug}-{prod_id}"
                results.append({"store": "Jumbo", "name": p.get('title'), "price": float(price), "volume": p.get('quantity', ''), "image": img, "link": link})
    except Exception as e:
            logger.warning(f"  Jumbo: Error: {e}")
            if DEBUG_MODE:
                logger.exception(f"  Jumbo: Exception details:")
    
    # Filter results to match search term
    search_lower = search_term.lower()
    if DEBUG_MODE:
        logger.debug(f"  Jumbo: Found {len(results)} total results before filtering")
    filtered_results = [r for r in results if search_lower in r['name'].lower()]
    if DEBUG_MODE and len(results) != len(filtered_results):
        logger.debug(f"  Jumbo: Filtered to {len(filtered_results)} results matching '{search_term}'")
    
    return filtered_results
