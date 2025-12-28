import httpx
from bs4 import BeautifulSoup
import urllib.parse
import logging
import os
import re
from app.utils import extract_price_from_text

DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
logger = logging.getLogger(__name__)

async def scrape_prikentik(search_term: str):
    results = []
    safe_term = urllib.parse.quote(search_term)
    url = f"https://www.prikentik.be/catalogsearch/result/?q={safe_term}"
    
    logger.info(f"🍺 Prik&Tik: Checking {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            # Get search results page
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            if DEBUG_MODE:
                logger.debug(f"  Prik&Tik: Page loaded successfully")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            products = soup.select('.product-item, li.product-item, .item.product')
            
            if DEBUG_MODE:
                logger.debug(f"  Prik&Tik: Found {len(products)} product tiles on search page")
            
            # Collect product links from search results
            product_links = []
            for prod in products:
                name_el = prod.select_one('.product-item-link, .product-name a, a.product-item-link, .product-item-name a')
                if name_el and name_el.get('href'):
                    product_links.append(name_el.get('href'))
            
            if DEBUG_MODE:
                logger.debug(f"  Prik&Tik: Collected {len(product_links)} product links, visiting each...")
            
            # Visit each product page to extract detailed information
            for idx, product_url in enumerate(product_links):
                try:
                    detail_response = await client.get(product_url, headers=headers)
                    detail_response.raise_for_status()
                    detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                    
                    # Extract product name from detail page
                    name = ""
                    name_el = detail_soup.select_one('h1.page-title, .product-name, h1')
                    if name_el:
                        name = name_el.get_text(strip=True)
                    
                    # Extract price from detail page (should be text, not image)
                    price = 0.0
                    price_el = detail_soup.select_one('.price, .price-wrapper .price, [data-price-type="finalPrice"]')
                    if price_el:
                        price_text = price_el.get_text(strip=True)
                        price = extract_price_from_text(price_text)
                    
                    # Try multiple image selectors
                    img = ""
                    img_el = detail_soup.select_one('.product-image-photo, .product-media img, .gallery-placeholder img, img')
                    if img_el:
                        for attr in ['data-original', 'data-src', 'data-lazy', 'srcset', 'src']:
                            img = img_el.get(attr, '')
                            if img:
                                break
                        # If srcset, take the first URL
                        if img and ' ' in img:
                            img = img.split()[0]
                        # Ensure complete URL
                        if img and not img.startswith('http'):
                            if img.startswith('//'):
                                img = f"https:{img}"
                            else:
                                img = f"https://www.prikentik.be{img}"
                    
                    if name:  # Only add if we got a name
                        results.append({
                            "store": "Prik&Tik",
                            "name": name.strip(),
                            "price": price,
                            "volume": "",
                            "image": img,
                            "link": product_url
                        })
                        
                        if DEBUG_MODE:
                            logger.debug(f"  Prik&Tik: [{idx+1}/{len(product_links)}] Extracted: {name[:50]} - €{price}")
                    
                except Exception as e:
                    if DEBUG_MODE:
                        logger.debug(f"  Prik&Tik: Error scraping product page {product_url}: {e}")
                        
    except Exception as e:
        logger.warning(f"  Prik&Tik: Scraping error: {e}")
        if DEBUG_MODE:
            logger.exception(f"  Prik&Tik: Exception details:")
    
    # Filter results to match search term (case-insensitive partial match)
    search_lower = search_term.lower()
    if DEBUG_MODE:
        logger.debug(f"  Prik&Tik: Found {len(results)} total results before filtering")
    filtered_results = [r for r in results if r.get('name') and search_lower in r['name'].lower()]
    if DEBUG_MODE and len(results) != len(filtered_results):
        logger.debug(f"  Prik&Tik: Filtered to {len(filtered_results)} results matching '{search_term}'")
    
    return filtered_results
