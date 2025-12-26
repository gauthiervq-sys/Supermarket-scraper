from playwright.async_api import async_playwright
import urllib.parse
import asyncio
import logging

# Default page timeout in milliseconds
DEFAULT_PAGE_TIMEOUT = 10000
logger = logging.getLogger(__name__)

async def scrape_lidl(search_term: str):
    results = []
    print(f"🟡 Lidl: Scanning...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        page.set_default_timeout(DEFAULT_PAGE_TIMEOUT)
        
        async def handle_response(response):
            url_lower = response.url.lower()
            if response.status == 200 and any(x in url_lower for x in ["search", "api", "product"]):
                try:
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        data = await response.json()
                        prods = data.get('results', []) or data.get('products', []) or data.get('items', [])
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
                                logger.debug(f"Error parsing Lidl product: {e}")
                except Exception as e:
                    logger.debug(f"Error parsing Lidl response: {e}")
        
        page.on("response", handle_response)
        safe_term = urllib.parse.quote(search_term)
        try:
            await page.goto(f"https://www.lidl.be/q/nl-BE/search?q={safe_term}", timeout=12000)
            try:
                accept_btn = await page.wait_for_selector('#onetrust-accept-btn-handler', timeout=2000)
                await accept_btn.click()
            except: pass
            # Wait for products with multiple selectors
            try:
                await page.wait_for_selector('article, .product-item, .product-card', timeout=5000)
            except: pass
            # Wait for response handlers to complete processing
            await asyncio.sleep(2)
            
            # Fallback: scrape from DOM if no API results
            if not results:
                articles = await page.query_selector_all('article, .product-item')
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
                        logger.debug(f"Error parsing Lidl product from DOM: {e}")
        except Exception as e:
            logger.warning(f"Lidl navigation error: {e}")
        await browser.close()
    
    # Filter results to match search term (case-insensitive partial match)
    search_lower = search_term.lower()
    filtered_results = [r for r in results if r.get('name') and search_lower in r['name'].lower()]
    return filtered_results
