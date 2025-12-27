from playwright.async_api import async_playwright
import urllib.parse
import asyncio
import logging
import os

# Default page timeout in milliseconds
DEFAULT_PAGE_TIMEOUT = 10000
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
logger = logging.getLogger(__name__)

async def scrape_ah(search_term: str):
    results = []
    safe_term = urllib.parse.quote(search_term)
    url = f"https://www.ah.be/zoeken?query={safe_term}"
    
    logger.info(f"🛒 Albert Heijn: Checking {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()
        page.set_default_timeout(DEFAULT_PAGE_TIMEOUT)
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        api_responses_received = []
        
        async def handle_response(response):
            url_lower = response.url.lower()
            if response.status == 200 and any(x in url_lower for x in ["search", "product", "zoeken", "api"]):
                api_responses_received.append(response.url)
                if DEBUG_MODE:
                    logger.debug(f"  AH: Intercepted API call: {response.url[:100]}...")
                try:
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        data = await response.json()
                        # Handle different API response structures
                        cards = data.get('cards', [])
                        if DEBUG_MODE and cards:
                            logger.debug(f"  AH: Found {len(cards)} cards in API response")
                        for card in cards:
                            for prod in card.get('products', []):
                                try:
                                    images = prod.get('images', [])
                                    img_url = images[0].get('url') if images else ""
                                    # Ensure image URL is complete
                                    if img_url and not img_url.startswith('http'):
                                        img_url = f"https://www.ah.be{img_url}"
                                    link_slug = prod.get('link', '')
                                    full_link = f"https://www.ah.be{link_slug}"
                                    
                                    name = prod.get('title', '')
                                    if name:  # Only add if we have a name
                                        results.append({
                                            "store": "Albert Heijn",
                                            "name": name,
                                            "price": float(prod.get('price', {}).get('now', 0.0)),
                                            "volume": prod.get('price', {}).get('unitSize', ''),
                                            "image": img_url,
                                            "link": full_link
                                        })
                                except Exception as e:
                                    if DEBUG_MODE:
                                        logger.debug(f"  AH: Error parsing product: {e}")
                        
                        # Also check for products array directly
                        products = data.get('products', [])
                        if DEBUG_MODE and products:
                            logger.debug(f"  AH: Found {len(products)} products in API response")
                        for prod in products:
                            try:
                                images = prod.get('images', [])
                                img_url = images[0].get('url') if images else ""
                                if img_url and not img_url.startswith('http'):
                                    img_url = f"https://www.ah.be{img_url}"
                                link_slug = prod.get('link', '')
                                full_link = f"https://www.ah.be{link_slug}"
                                
                                name = prod.get('title', prod.get('name', ''))
                                if name:
                                    results.append({
                                        "store": "Albert Heijn",
                                        "name": name,
                                        "price": float(prod.get('price', {}).get('now', prod.get('price', {}).get('value', 0.0))),
                                        "volume": prod.get('price', {}).get('unitSize', prod.get('unitSize', '')),
                                        "image": img_url,
                                        "link": full_link
                                    })
                            except Exception as e:
                                if DEBUG_MODE:
                                    logger.debug(f"  AH: Error parsing product: {e}")
                except Exception as e:
                    if DEBUG_MODE:
                        logger.debug(f"  AH: Error parsing response: {e}")
        
        page.on("response", handle_response)
        try:
            await page.goto(url, timeout=15000, wait_until="networkidle")
            if DEBUG_MODE:
                logger.debug(f"  AH: Page loaded, waiting for content")
            
            try:
                await page.click('#accept-cookies', timeout=2000)
                await asyncio.sleep(0.5)
                if DEBUG_MODE:
                    logger.debug(f"  AH: Accepted cookies")
            except: pass
            
            # Wait for products to load with multiple selectors
            try:
                await page.wait_for_selector('article[data-test-id="product-card"], .product-card, [data-testid="product"], article', timeout=6000)
                if DEBUG_MODE:
                    logger.debug(f"  AH: Products loaded on page")
            except:
                if DEBUG_MODE:
                    logger.debug(f"  AH: No product elements found on page")
            
            # Scroll to trigger lazy loading
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await asyncio.sleep(1)
            
            # Wait for response handlers to complete processing
            await asyncio.sleep(3)
            
            if DEBUG_MODE:
                logger.debug(f"  AH: Received {len(api_responses_received)} API responses")
        except Exception as e:
            logger.warning(f"  AH: Navigation error: {e}")
        await browser.close()
    
    # Filter results to match search term (case-insensitive partial match)
    search_lower = search_term.lower()
    if DEBUG_MODE:
        logger.debug(f"  AH: Found {len(results)} total results before filtering")
    filtered_results = [r for r in results if r.get('name') and search_lower in r['name'].lower()]
    if DEBUG_MODE and len(results) != len(filtered_results):
        logger.debug(f"  AH: Filtered to {len(filtered_results)} results matching '{search_term}'")
    
    return filtered_results
