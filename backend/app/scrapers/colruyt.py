from playwright.async_api import async_playwright
import urllib.parse
import asyncio
import logging
import os

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
        
        async def handle_response(response):
            # Look for various API endpoints that might contain product data
            url_lower = response.url.lower()
            if response.status == 200 and any(x in url_lower for x in ["productview", "search", "product"]):
                if DEBUG_MODE:
                    logger.debug(f"  Colruyt: Intercepted API call: {response.url[:80]}...")
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
            await page.goto(url, timeout=12000)
            try:
                accept_btn = await page.wait_for_selector('#onetrust-accept-btn-handler', timeout=2000)
                await accept_btn.click()
                if DEBUG_MODE:
                    logger.debug(f"  Colruyt: Accepted cookies")
            except: pass
            # Wait for products to load
            try:
                await page.wait_for_selector('.product-card, .product-item, [data-testid="product"]', timeout=5000)
                if DEBUG_MODE:
                    logger.debug(f"  Colruyt: Products loaded on page")
            except:
                if DEBUG_MODE:
                    logger.debug(f"  Colruyt: No product elements found on page")
            # Wait for response handlers to complete processing
            await asyncio.sleep(2)
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
