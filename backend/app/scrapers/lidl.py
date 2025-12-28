import httpx
from bs4 import BeautifulSoup
import urllib.parse
import logging
import os
import re

DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
logger = logging.getLogger(__name__)

async def scrape_lidl(search_term: str):
    results = []
    safe_term = urllib.parse.quote(search_term)
    url = f"https://www.lidl.be/q/nl-BE/search?q={safe_term}"
    
    logger.info(f"🟡 Lidl: Checking {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            if DEBUG_MODE:
                logger.debug(f"  Lidl: Page loaded successfully")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.select('article, .product-item')
            
            if DEBUG_MODE:
                logger.debug(f"  Lidl: Found {len(articles)} product elements in DOM")
            
            for article in articles:
                try:
                    name_el = article.select_one('h3, h2, .product-title')
                    name = name_el.get_text(strip=True) if name_el else ""
                    
                    if not name:
                        continue
                    
                    # Extract price
                    price = 0.0
                    price_el = article.select_one('.price, [data-testid="price"]')
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
                    img_el = article.select_one('img')
                    img = ""
                    if img_el:
                        img = img_el.get('data-src', img_el.get('src', ''))
                    if img and not img.startswith('http'):
                        if img.startswith('//'):
                            img = f"https:{img}"
                        else:
                            img = f"https://www.lidl.be{img}"
                    
                    # Extract link
                    link_el = article.select_one('a')
                    link = link_el.get('href', '') if link_el else ""
                    if link and not link.startswith('http'):
                        link = f"https://www.lidl.be{link}"
                    
                    results.append({
                        "store": "Lidl",
                        "name": name.strip(),
                        "price": price,
                        "volume": "",
                        "image": img,
                        "link": link
                    })
                except Exception as e:
                    if DEBUG_MODE:
                        logger.debug(f"  Lidl: Error parsing product from DOM: {e}")
    except Exception as e:
        logger.warning(f"  Lidl: Navigation error: {e}")
        if DEBUG_MODE:
            logger.exception(f"  Lidl: Exception details:")
    
    # Filter results to match search term (case-insensitive partial match)
    search_lower = search_term.lower()
    if DEBUG_MODE:
        logger.debug(f"  Lidl: Found {len(results)} total results before filtering")
    filtered_results = [r for r in results if r.get('name') and search_lower in r['name'].lower()]
    if DEBUG_MODE and len(results) != len(filtered_results):
        logger.debug(f"  Lidl: Filtered to {len(filtered_results)} results matching '{search_term}'")
    
    return filtered_results
