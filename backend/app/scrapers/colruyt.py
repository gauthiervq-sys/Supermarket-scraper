from playwright.async_api import async_playwright
import urllib.parse
import asyncio
import logging
import os
from app.ocr_utils import extract_price_from_element_with_ocr_fallback

# Default page timeout in milliseconds
DEFAULT_PAGE_TIMEOUT = 10000
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
logger = logging.getLogger(__name__)

async def scrape_colruyt(search_term: str):
    results = []
    safe_term = urllib.parse.quote(search_term)
    url = f"https://www.collectandgo.be/nl/zoek?searchTerm={safe_term}"
    
    logger.info(f"🛒 Colruyt: Checking {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        page.set_default_timeout(DEFAULT_PAGE_TIMEOUT)
        
        api_responses_received = []
        
        async def handle_response(response):
            # Look for various API endpoints that might contain product data
            url_lower = response.url.lower()
            if response.status == 200 and any(x in url_lower for x in ["productview", "search", "product", "article", "zoek"]):
                api_responses_received.append(response.url)
                if DEBUG_MODE:
                    logger.debug(f"  Colruyt: Intercepted API call: {response.url[:100]}...")
                try:
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        data = await response.json()
                        # Handle different API response structures
                        products = data.get('catalogEntryView', []) or data.get('products', []) or data.get('items', [])
                        if DEBUG_MODE and products:
                            logger.debug(f"  Colruyt: Found {len(products)} products in API response")
                        for item in products:
                            try:
                                price_data = item.get('price', [])
                                if isinstance(price_data, list) and price_data:
                                    price = price_data[0].get('offerPrice', 0.0)
                                elif isinstance(price_data, dict):
                                    price = price_data.get('offerPrice', price_data.get('value', 0.0))
                                else:
                                    price = item.get('price', 0.0)
                                
                                prod_id = item.get('uniqueID', item.get('id', ''))
                                link = f"https://www.collectandgo.be/site/nl/artikel-detail/{prod_id}"
                                img_url = item.get('fullImage', item.get('image', ''))
                                # Ensure image URL is complete
                                if img_url and not img_url.startswith('http'):
                                    img_url = f"https://www.collectandgo.be{img_url}"
                                
                                name = item.get('name', item.get('title', ''))
                                if name:  # Only add if we have a name
                                    results.append({
                                        "store": "Colruyt",
                                        "name": name,
                                        "price": float(price) if price else 0.0,
                                        "volume": item.get('content', item.get('volume', '')),
                                        "image": img_url,
                                        "link": link
                                    })
                            except Exception as e:
                                if DEBUG_MODE:
                                    logger.debug(f"  Colruyt: Error parsing product: {e}")
                except Exception as e:
                    if DEBUG_MODE:
                        logger.debug(f"  Colruyt: Error parsing response: {e}")
        
        page.on("response", handle_response)
        try:
            await page.goto(url, timeout=15000, wait_until="networkidle")
            if DEBUG_MODE:
                logger.debug(f"  Colruyt: Page loaded, waiting for content")
            
            try:
                accept_btn = await page.wait_for_selector('#onetrust-accept-btn-handler', timeout=2000)
                await accept_btn.click()
                await asyncio.sleep(0.5)
                if DEBUG_MODE:
                    logger.debug(f"  Colruyt: Accepted cookies")
            except: pass
            
            # Wait for products to load with multiple attempts
            try:
                await page.wait_for_selector('.product-card, .product-item, [data-testid="product"], article', timeout=6000)
                if DEBUG_MODE:
                    logger.debug(f"  Colruyt: Products loaded on page")
            except:
                if DEBUG_MODE:
                    logger.debug(f"  Colruyt: No product elements found on page")
            
            # Scroll to trigger lazy loading
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await asyncio.sleep(1)
            
            # Wait longer for response handlers to complete processing
            await asyncio.sleep(3)
            
            if DEBUG_MODE:
                logger.debug(f"  Colruyt: Received {len(api_responses_received)} API responses")
            
            # Fallback: scrape from DOM if no API results
            if not results:
                if DEBUG_MODE:
                    logger.debug(f"  Colruyt: No API results, trying DOM scraping")
                cards = await page.query_selector_all('.product-card, .product-item, article, [data-testid="product"]')
                if DEBUG_MODE:
                    logger.debug(f"  Colruyt: Found {len(cards)} product cards in DOM")
                for card in cards:
                    try:
                        name_el = await card.query_selector('.product-name, .product-title, h3, h2, a[class*="title"], a[class*="name"]')
                        name = await name_el.inner_text() if name_el else ""
                        if not name:
                            continue
                        
                        price_el = await card.query_selector('.price, [class*="price"], [data-testid="price"]')
                        price = 0.0
                        if price_el:
                            price = await extract_price_from_element_with_ocr_fallback(page, price_el, name, DEBUG_MODE)
                        
                        link_el = await card.query_selector('a')
                        link_href = await link_el.get_attribute('href') if link_el else ""
                        if link_href and not link_href.startswith('http'):
                            link_href = f"https://www.collectandgo.be{link_href}"
                        
                        img_el = await card.query_selector('img')
                        img = ""
                        if img_el:
                            img = await img_el.get_attribute('data-src') or await img_el.get_attribute('src') or ""
                        if img and not img.startswith('http'):
                            if img.startswith('//'):
                                img = f"https:{img}"
                            else:
                                img = f"https://www.collectandgo.be{img}"
                        
                        results.append({
                            "store": "Colruyt",
                            "name": name.strip(),
                            "price": price,
                            "volume": "",
                            "image": img,
                            "link": link_href
                        })
                    except Exception as e:
                        if DEBUG_MODE:
                            logger.debug(f"  Colruyt: Error parsing product from DOM: {e}")
        except Exception as e:
            logger.warning(f"  Colruyt: Navigation error: {e}")
        await browser.close()
    
    # Filter results to match search term (case-insensitive partial match)
    search_lower = search_term.lower()
    if DEBUG_MODE:
        logger.debug(f"  Colruyt: Found {len(results)} total results before filtering")
    filtered_results = [r for r in results if r.get('name') and search_lower in r['name'].lower()]
    if DEBUG_MODE and len(results) != len(filtered_results):
        logger.debug(f"  Colruyt: Filtered to {len(filtered_results)} results matching '{search_term}'")
    
    return filtered_results
