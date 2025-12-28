import httpx
from bs4 import BeautifulSoup
import urllib.parse
import logging
import os
import re

DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
logger = logging.getLogger(__name__)

async def scrape_carrefour(search_term: str):
    results = []
    safe_term = urllib.parse.quote(search_term)
    url = f"https://www.carrefour.be/nl/search?q={safe_term}"
    
    logger.info(f"🟠 Carrefour: Checking {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            if DEBUG_MODE:
                logger.debug(f"  Carrefour: Page loaded successfully")
                logger.debug(f"  Carrefour: HTML content length: {len(response.text)} characters")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Log the actual text content to help diagnose issues
            if DEBUG_MODE:
                body = soup.find('body')
                if body:
                    body_text = body.get_text(strip=True, separator=' ')
                    logger.debug(f"  Carrefour: Page body text (first 500 chars): {body_text[:500]}")
                    logger.debug(f"  Carrefour: Page body text (last 500 chars): {body_text[-500:]}")
                else:
                    logger.debug(f"  Carrefour: No <body> tag found in HTML")
                
                # Check for JavaScript-rendered content indicators
                if any(indicator in response.text for indicator in ['window.__', 'React', 'Vue', 'Angular', '__NEXT_DATA__']):
                    logger.debug(f"  Carrefour: ⚠️  Site appears to use JavaScript rendering")
            
            cards = soup.select('.product-card, .product-item, article')
            
            if DEBUG_MODE:
                logger.debug(f"  Carrefour: Found {len(cards)} product cards in DOM")
                if len(cards) == 0:
                    # Try to show what elements ARE in the page
                    all_elements = soup.find_all(True, limit=20)
                    element_tags = [f"<{el.name}>" for el in all_elements]
                    logger.debug(f"  Carrefour: First 20 HTML elements found: {', '.join(element_tags)}")
                    # Show the raw HTML structure (first 1000 chars)
                    logger.debug(f"  Carrefour: Raw HTML structure (first 1000 chars): {response.text[:1000]}")
            
            for card in cards:
                try:
                    name_el = card.select_one('.product-card__title, .product-title, h3, h2, a')
                    name = name_el.get_text(strip=True) if name_el else ""
                    
                    if not name:
                        continue
                    
                    # Extract price
                    price = 0.0
                    price_el = card.select_one('.product-card-price__price, .price, [data-testid="price"], [class*="price"]')
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
                    link_el = card.select_one('a.product-card__title-link, a')
                    link_href = link_el.get('href', '') if link_el else ""
                    if link_href and not link_href.startswith('http'):
                        link_href = f"https://www.carrefour.be{link_href}"
                    
                    # Extract image
                    img_el = card.select_one('img')
                    img = ""
                    if img_el:
                        img = img_el.get('data-src', img_el.get('src', ''))
                    # Ensure image URL is complete
                    if img and not img.startswith('http'):
                        if img.startswith('//'):
                            img = f"https:{img}"
                        else:
                            img = f"https://www.carrefour.be{img}"
                    
                    results.append({
                        "store": "Carrefour",
                        "name": name.strip(),
                        "price": price,
                        "volume": "",
                        "image": img,
                        "link": link_href
                    })
                except Exception as e:
                    if DEBUG_MODE:
                        logger.debug(f"  Carrefour: Error parsing product from DOM: {e}")
    except Exception as e:
        logger.warning(f"  Carrefour: Navigation error: {e}")
        if DEBUG_MODE:
            logger.exception(f"  Carrefour: Exception details:")
    
    # Filter results to match search term (case-insensitive partial match)
    search_lower = search_term.lower()
    if DEBUG_MODE:
        logger.debug(f"  Carrefour: Found {len(results)} total results before filtering")
    filtered_results = [r for r in results if r.get('name') and search_lower in r['name'].lower()]
    if DEBUG_MODE and len(results) != len(filtered_results):
        logger.debug(f"  Carrefour: Filtered to {len(filtered_results)} results matching '{search_term}'")
    
    return filtered_results
