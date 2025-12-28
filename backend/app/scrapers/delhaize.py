import httpx
from bs4 import BeautifulSoup
import urllib.parse
import logging
import os
import re
from app.utils import log_scraped_html_debug

DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
logger = logging.getLogger(__name__)

async def scrape_delhaize(search_term: str):
    results = []
    safe_term = urllib.parse.quote(search_term)
    url = f"https://www.delhaize.be/nl/shop/search?q={safe_term}"
    
    logger.info(f"🦁 Delhaize: Checking {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            if DEBUG_MODE:
                logger.debug(f"  Delhaize: Page loaded successfully")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            cards = soup.select('li[data-test="product-card"], .product-card, .product-item, article')
            
            # Log detailed HTML debugging information
            log_scraped_html_debug(logger, "Delhaize", response.text, soup, len(cards))
            
            if DEBUG_MODE:
                logger.debug(f"  Delhaize: Found {len(cards)} product cards in DOM")
            
            for card in cards:
                try:
                    name_el = card.select_one('[data-test="product-title"], .product-title, h3, h2, a')
                    name = name_el.get_text(strip=True) if name_el else ""
                    
                    if not name:
                        continue
                    
                    # Extract price
                    price = 0.0
                    price_el = card.select_one('[data-test="price"], .price, [class*="price"]')
                    if price_el:
                        price_txt = price_el.get_text(strip=True)
                        # Remove currency symbols and convert to float
                        price_txt = re.sub(r'[^\d,.]', '', price_txt)
                        price_txt = price_txt.replace(',', '.')
                        try:
                            price = float(price_txt)
                        except ValueError:
                            price = 0.0
                    
                    # Extract image
                    img_el = card.select_one('img')
                    img = ""
                    if img_el:
                        img = img_el.get('data-src', img_el.get('src', ''))
                    if img and not img.startswith('http'):
                        if img.startswith('//'):
                            img = f"https:{img}"
                        else:
                            img = f"https://www.delhaize.be{img}"
                    
                    # Extract link
                    link_el = card.select_one('a')
                    link = link_el.get('href', '') if link_el else ""
                    if link and not link.startswith('http'):
                        link = f"https://www.delhaize.be{link}"
                    
                    results.append({
                        "store": "Delhaize",
                        "name": name.strip(),
                        "price": price,
                        "volume": "",
                        "image": img,
                        "link": link
                    })
                except Exception as e:
                    if DEBUG_MODE:
                        logger.debug(f"  Delhaize: Error parsing product from DOM: {e}")
    except Exception as e:
        logger.warning(f"  Delhaize: Navigation error: {e}")
        if DEBUG_MODE:
            logger.exception(f"  Delhaize: Exception details:")
    
    # Filter results to match search term (case-insensitive partial match)
    search_lower = search_term.lower()
    if DEBUG_MODE:
        logger.debug(f"  Delhaize: Found {len(results)} total results before filtering")
    filtered_results = [r for r in results if r.get('name') and search_lower in r['name'].lower()]
    if DEBUG_MODE and len(results) != len(filtered_results):
        logger.debug(f"  Delhaize: Filtered to {len(filtered_results)} results matching '{search_term}'")
    
    return filtered_results
