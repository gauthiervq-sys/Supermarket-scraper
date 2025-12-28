import httpx
from bs4 import BeautifulSoup
import urllib.parse
import logging
import os
import re

DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
logger = logging.getLogger(__name__)

async def scrape_woocommerce(store_name, base_url, search_term):
    results = []
    safe_term = urllib.parse.quote(search_term)
    url = f"{base_url}?s={safe_term}&post_type=product"
    
    logger.info(f"📦 {store_name}: Checking {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            if DEBUG_MODE:
                logger.debug(f"  {store_name}: Page loaded successfully (status {response.status_code})")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            products = soup.select('.product')
            
            if DEBUG_MODE:
                logger.debug(f"  {store_name}: Found {len(products)} product elements on page")
            
            for prod in products:
                try:
                    # Extract product name
                    title_el = prod.select_one('.woocommerce-loop-product__title, .product-title, h3, h2')
                    name = title_el.get_text(strip=True) if title_el else ""
                    
                    if not name:
                        continue
                    
                    # Extract price
                    price = 0.0
                    price_el = prod.select_one('span.price bdi, .price .amount, .price')
                    if price_el:
                        price_txt = price_el.get_text(strip=True)
                        # Remove currency symbols and convert to float
                        price_txt = re.sub(r'[^\d,.]', '', price_txt)
                        price_txt = price_txt.replace(',', '.')
                        try:
                            price = float(price_txt)
                        except ValueError:
                            price = 0.0
                    
                    # Extract link
                    link_el = prod.select_one('a')
                    link = link_el.get('href', '') if link_el else ""
                    
                    # Extract image
                    img_el = prod.select_one('img')
                    img = ''
                    if img_el:
                        img = img_el.get('src', img_el.get('data-src', ''))
                    
                    # Ensure image URL is complete
                    if img and not img.startswith('http'):
                        if img.startswith('/'):
                            img = f"{base_url.rstrip('/')}{img}"
                        else:
                            img = f"{base_url}{img}"
                    
                    results.append({
                        "store": store_name,
                        "name": name.strip(),
                        "price": price,
                        "volume": "",
                        "image": img,
                        "link": link
                    })
                except Exception as e:
                    if DEBUG_MODE:
                        logger.debug(f"  {store_name}: Error parsing product: {e}")
    except Exception as e:
        logger.warning(f"  {store_name}: Scraping error: {e}")
        if DEBUG_MODE:
            logger.exception(f"  {store_name}: Exception details:")
    
    # Filter results to match search term
    search_lower = search_term.lower()
    if DEBUG_MODE:
        logger.debug(f"  {store_name}: Found {len(results)} total results before filtering")
    filtered_results = [r for r in results if search_lower in r['name'].lower()]
    if DEBUG_MODE and len(results) != len(filtered_results):
        logger.debug(f"  {store_name}: Filtered to {len(filtered_results)} results matching '{search_term}'")
    
    return filtered_results

async def scrape_snuffelstore(q): return await scrape_woocommerce("Snuffelstore", "https://www.snuffelstore.be/", q)
async def scrape_drinkscorner(q): return await scrape_woocommerce("Drinks Corner", "https://drinkscorner.be/", q)
