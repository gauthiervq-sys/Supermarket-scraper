from playwright.async_api import async_playwright
import urllib.parse
import asyncio
import logging
import os

# Default page timeout in milliseconds
DEFAULT_PAGE_TIMEOUT = 10000
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
logger = logging.getLogger(__name__)

async def scrape_delhaize(search_term: str):
    results = []
    safe_term = urllib.parse.quote(search_term)
    url = f"https://www.delhaize.be/nl/shop/search?q={safe_term}"
    
    logger.info(f"🦁 Delhaize: Checking {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        page.set_default_timeout(DEFAULT_PAGE_TIMEOUT)
        
        api_responses_received = []
        
        async def handle_response(response):
            url_lower = response.url.lower()
            if response.status == 200 and any(x in url_lower for x in ["search", "product", "api", "graphql"]):
                api_responses_received.append(response.url)
                if DEBUG_MODE:
                    logger.debug(f"  Delhaize: Intercepted API call: {response.url[:100]}...")
                try:
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        data = await response.json()
                        items = data.get('products', []) or data.get('results', []) or data.get('items', [])
                        if DEBUG_MODE and items:
                            logger.debug(f"  Delhaize: Found {len(items)} products in API response")
                        for item in items:
                            try:
                                name = item.get('name', item.get('title', 'Naamloos'))
                                price = item.get('price', {}).get('value', 0.0) if isinstance(item.get('price'), dict) else item.get('price', 0.0)
                                code = item.get('code', item.get('id', ''))
                                link = f"https://www.delhaize.be/nl/shop/p/{code}" if code else ""
                                
                                # Handle image URL
                                img = ""
                                if item.get('images'):
                                    img = item.get('images', [{}])[0].get('url', '')
                                elif item.get('image'):
                                    img = item.get('image', '')
                                # Ensure image URL is complete
                                if img and not img.startswith('http'):
                                    img = f"https://www.delhaize.be{img}"
                                
                                if name and name != 'Naamloos':
                                    results.append({
                                        "store": "Delhaize",
                                        "name": name,
                                        "price": float(price) if price else 0.0,
                                        "volume": item.get('measurementUnit', item.get('volume', item.get('unitSize', ''))),
                                        "image": img,
                                        "link": link
                                    })
                            except Exception as e:
                                if DEBUG_MODE:
                                    logger.debug(f"  Delhaize: Error parsing product: {e}")
                except Exception as e:
                    if DEBUG_MODE:
                        logger.debug(f"  Delhaize: Error parsing response: {e}")
        
        page.on("response", handle_response)
        try:
            await page.goto(url, timeout=15000, wait_until="networkidle")
            if DEBUG_MODE:
                logger.debug(f"  Delhaize: Page loaded, waiting for content")
            
            try:
                accept_btn = await page.wait_for_selector('#onetrust-accept-btn-handler', timeout=2000)
                await accept_btn.click()
                await asyncio.sleep(0.5)
                if DEBUG_MODE:
                    logger.debug(f"  Delhaize: Accepted cookies")
            except: pass
            
            # Wait for products with multiple selectors
            try:
                await page.wait_for_selector('li[data-test="product-card"], .product-card, .product-item, article', timeout=6000)
                if DEBUG_MODE:
                    logger.debug(f"  Delhaize: Products loaded on page")
            except:
                if DEBUG_MODE:
                    logger.debug(f"  Delhaize: No product elements found on page")
            
            # Scroll to trigger lazy loading
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await asyncio.sleep(1)
            
            # Wait longer for response handlers to complete processing
            await asyncio.sleep(3)
            
            if DEBUG_MODE:
                logger.debug(f"  Delhaize: Received {len(api_responses_received)} API responses")
            
            # Fallback: scrape from DOM if no API results
            if not results:
                if DEBUG_MODE:
                    logger.debug(f"  Delhaize: No API results, trying DOM scraping")
                cards = await page.query_selector_all('li[data-test="product-card"], .product-card, .product-item, article')
                if DEBUG_MODE:
                    logger.debug(f"  Delhaize: Found {len(cards)} product cards in DOM")
                for card in cards:
                    try:
                        name_el = await card.query_selector('[data-test="product-title"], .product-title, h3, h2, a')
                        name = await name_el.inner_text() if name_el else ""
                        price_el = await card.query_selector('[data-test="price"], .price, [class*="price"]')
                        price = 0.0
                        if price_el:
                            price_txt = await price_el.inner_text()
                            price = float(price_txt.replace('€', '').replace(',', '.').strip())
                        img_el = await card.query_selector('img')
                        img = ""
                        if img_el:
                            img = await img_el.get_attribute('data-src') or await img_el.get_attribute('src') or ""
                        if img and not img.startswith('http'):
                            img = f"https://www.delhaize.be{img}"
                        link_el = await card.query_selector('a')
                        link = await link_el.get_attribute('href') if link_el else ""
                        if link and not link.startswith('http'):
                            link = f"https://www.delhaize.be{link}"
                        if name:
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
        await browser.close()
    
    # Filter results to match search term (case-insensitive partial match)
    search_lower = search_term.lower()
    if DEBUG_MODE:
        logger.debug(f"  Delhaize: Found {len(results)} total results before filtering")
    filtered_results = [r for r in results if r.get('name') and search_lower in r['name'].lower()]
    if DEBUG_MODE and len(results) != len(filtered_results):
        logger.debug(f"  Delhaize: Filtered to {len(filtered_results)} results matching '{search_term}'")
    
    return filtered_results
