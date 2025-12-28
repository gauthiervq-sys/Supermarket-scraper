import httpx
from bs4 import BeautifulSoup
import urllib.parse
import logging
import os
import re
from app.utils import extract_price_from_text

DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
logger = logging.getLogger(__name__)

async def scrape_aldi(search_term: str):
    results = []
    safe_term = urllib.parse.quote(search_term)
    url = f"https://www.aldi.be/nl/zoekresultaten.html?query={safe_term}&searchCategory=Submitted%20Search"
    
    logger.info(f"🛒 Aldi: Checking {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            # Get search results page
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            if DEBUG_MODE:
                logger.debug(f"  Aldi: Page loaded successfully")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            products = soup.select('.mod-article-tile')
            
            if DEBUG_MODE:
                logger.debug(f"  Aldi: Found {len(products)} product tiles on search page")
            
            # Collect product links from search results
            product_links = []
            for prod in products:
                link_el = prod.select_one('a')
                if link_el and link_el.get('href'):
                    link_href = link_el.get('href')
                    if not link_href.startswith('http'):
                        link_href = f"https://www.aldi.be{link_href}"
                    product_links.append(link_href)
            
            if DEBUG_MODE:
                logger.debug(f"  Aldi: Collected {len(product_links)} product links, visiting each...")
            
            # Visit each product page to extract detailed information
            for idx, product_url in enumerate(product_links):
                try:
                    detail_response = await client.get(product_url, headers=headers)
                    detail_response.raise_for_status()
                    detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                    
                    # Extract product name
                    name_el = detail_soup.select_one('h1, .product-title, .mod-article-tile__title')
                    name = name_el.get_text(strip=True) if name_el else ""
                    
                    # Extract price from detail page
                    price = 0.0
                    price_wrapper = detail_soup.select_one('.price__wrapper, .price, [class*="price"]')
                    if price_wrapper:
                        price_text = price_wrapper.get_text(strip=True)
                        price = extract_price_from_text(price_text)
                    
                    # Extract volume/quantity
                    volume = ""
                    quantity_el = detail_soup.select_one('.mod-article-tile__quantity, .product-quantity, [class*="quantity"]')
                    if quantity_el:
                        volume = quantity_el.get_text(strip=True)
                    if not volume:
                        subtitle_el = detail_soup.select_one('.mod-article-tile__subtitle, .product-subtitle')
                        if subtitle_el:
                            volume = subtitle_el.get_text(strip=True)
                    
                    # Extract image
                    img_src = ""
                    img_el = detail_soup.select_one('img.product-image, .product-image img, img')
                    if img_el:
                        img_src = img_el.get('src', img_el.get('data-src', ''))
                        if img_src and not img_src.startswith('http'):
                            img_src = f"https://www.aldi.be{img_src}"
                    
                    if name:  # Only add if we got a name
                        results.append({
                            "store": "Aldi",
                            "name": name.strip(),
                            "price": price,
                            "volume": volume.strip(),
                            "image": img_src,
                            "link": product_url
                        })
                        
                        if DEBUG_MODE:
                            logger.debug(f"  Aldi: [{idx+1}/{len(product_links)}] Extracted: {name[:50]} - €{price}")
                    
                except Exception as e:
                    if DEBUG_MODE:
                        logger.debug(f"  Aldi: Error scraping product page {product_url}: {e}")
                        
    except Exception as e:
        logger.warning(f"  Aldi: Navigation error: {e}")
        if DEBUG_MODE:
            logger.exception(f"  Aldi: Exception details:")
    
    # Filter results to match search term
    search_lower = search_term.lower()
    if DEBUG_MODE:
        logger.debug(f"  Aldi: Found {len(results)} total results before filtering")
    filtered_results = [r for r in results if search_lower in r['name'].lower()]
    if DEBUG_MODE and len(results) != len(filtered_results):
        logger.debug(f"  Aldi: Filtered to {len(filtered_results)} results matching '{search_term}'")
    
    return filtered_results
