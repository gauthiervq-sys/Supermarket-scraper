from playwright.async_api import async_playwright
import urllib.parse
import asyncio
import logging
import os

# Default page timeout in milliseconds
DEFAULT_PAGE_TIMEOUT = 10000
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
logger = logging.getLogger(__name__)

async def scrape_lidl(search_term: str):
    results = []
    safe_term = urllib.parse.quote(search_term)
    url = f"https://www.lidl.be/q/nl-BE/search?q={safe_term}"
    
    logger.info(f"🟡 Lidl: Checking {url}")
    
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
            if response.status == 200 and any(x in url_lower for x in ["search", "api", "product", "graphql"]):
                api_responses_received.append(response.url)
                if DEBUG_MODE:
                    logger.debug(f"  Lidl: Intercepted API call: {response.url[:100]}...")
                try:
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        data = await response.json()
                        prods = data.get('results', []) or data.get('products', []) or data.get('items', [])
                        if DEBUG_MODE and prods:
                            logger.debug(f"  Lidl: Found {len(prods)} products in API response")
                        for item in prods:
                            try:
                                name = item.get('keyfacts', {}).get('title', '') or item.get('fullTitle', '') or item.get('name', '') or item.get('title', '')
                                price = item.get('price', {}).get('price', 0.0) if isinstance(item.get('price'), dict) else item.get('price', 0.0)
                                img = item.get('image', item.get('imageUrl', ''))
                                # Ensure image URL is complete
                                if img and not img.startswith('http'):
                                    img = f"https://www.lidl.be{img}"
                                prod_id = item.get('productId', item.get('id', ''))
                                link = f"https://www.lidl.be/p/{prod_id}" if prod_id else f"https://www.lidl.be/q/nl-BE/search?q={search_term}"
                                if name:
                                    results.append({
                                        "store": "Lidl",
                                        "name": name,
                                        "price": float(price) if isinstance(price, (int, float)) else 0.0,
                                        "volume": item.get('volume', item.get('unitSize', '')),
                                        "image": img,
                                        "link": link
                                    })
                            except Exception as e:
                                if DEBUG_MODE:
                                    logger.debug(f"  Lidl: Error parsing product: {e}")
                except Exception as e:
                    if DEBUG_MODE:
                        logger.debug(f"  Lidl: Error parsing response: {e}")
        
        page.on("response", handle_response)
        try:
            await page.goto(url, timeout=15000, wait_until="networkidle")
            if DEBUG_MODE:
                logger.debug(f"  Lidl: Page loaded, waiting for content")
            
            try:
                accept_btn = await page.wait_for_selector('#onetrust-accept-btn-handler', timeout=2000)
                await accept_btn.click()
                await asyncio.sleep(0.5)
                if DEBUG_MODE:
                    logger.debug(f"  Lidl: Accepted cookies")
            except: pass
            
            # Wait for products with multiple selectors
            try:
                await page.wait_for_selector('article, .product-item, .product-card', timeout=6000)
                if DEBUG_MODE:
                    logger.debug(f"  Lidl: Products loaded on page")
            except:
                if DEBUG_MODE:
                    logger.debug(f"  Lidl: No product elements found on page")
            
            # Scroll to trigger lazy loading
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await asyncio.sleep(1)
            
            # Wait for response handlers to complete processing
            await asyncio.sleep(3)
            
            if DEBUG_MODE:
                logger.debug(f"  Lidl: Received {len(api_responses_received)} API responses")
            
            # Fallback: scrape from DOM if no API results
            if not results:
                if DEBUG_MODE:
                    logger.debug(f"  Lidl: No API results, trying DOM scraping")
                articles = await page.query_selector_all('article, .product-item')
                if DEBUG_MODE:
                    logger.debug(f"  Lidl: Found {len(articles)} product elements in DOM")
                for article in articles:
                    try:
                        name_el = await article.query_selector('h3, h2, .product-title')
                        name = await name_el.inner_text() if name_el else ""
                        price_el = await article.query_selector('.price, [data-testid="price"]')
                        price = 0.0
                        if price_el:
                            price_txt = await price_el.inner_text()
                            price = float(price_txt.replace('€', '').replace(',', '.').strip())
                        img_el = await article.query_selector('img')
                        img = ""
                        if img_el:
                            img = await img_el.get_attribute('data-src') or await img_el.get_attribute('src') or ""
                        if img and not img.startswith('http'):
                            img = f"https://www.lidl.be{img}"
                        link_el = await article.query_selector('a')
                        link = await link_el.get_attribute('href') if link_el else ""
                        if link and not link.startswith('http'):
                            link = f"https://www.lidl.be{link}"
                        if name:
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
        await browser.close()
    
    # Filter results to match search term (case-insensitive partial match)
    search_lower = search_term.lower()
    if DEBUG_MODE:
        logger.debug(f"  Lidl: Found {len(results)} total results before filtering")
    filtered_results = [r for r in results if r.get('name') and search_lower in r['name'].lower()]
    if DEBUG_MODE and len(results) != len(filtered_results):
        logger.debug(f"  Lidl: Filtered to {len(filtered_results)} results matching '{search_term}'")
    
    return filtered_results
