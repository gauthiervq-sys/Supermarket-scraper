from playwright.async_api import async_playwright
import urllib.parse
import asyncio
import logging

# Default page timeout in milliseconds
DEFAULT_PAGE_TIMEOUT = 10000
logger = logging.getLogger(__name__)

async def scrape_delhaize(search_term: str):
    results = []
    print(f"🦁 Delhaize: Scanning...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        page.set_default_timeout(DEFAULT_PAGE_TIMEOUT)
        
        async def handle_response(response):
            url_lower = response.url.lower()
            if response.status == 200 and any(x in url_lower for x in ["search", "product"]):
                try:
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        data = await response.json()
                        items = data.get('products', []) or data.get('results', []) or data.get('items', [])
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
                                logger.debug(f"Error parsing Delhaize product: {e}")
                except Exception as e:
                    logger.debug(f"Error parsing Delhaize response: {e}")
        
        page.on("response", handle_response)
        safe_term = urllib.parse.quote(search_term)
        try:
            await page.goto(f"https://www.delhaize.be/nl/shop/search?q={safe_term}", timeout=12000)
            try:
                accept_btn = await page.wait_for_selector('#onetrust-accept-btn-handler', timeout=2000)
                await accept_btn.click()
            except: pass
            # Wait for products with multiple selectors
            try:
                await page.wait_for_selector('li[data-test="product-card"], .product-card, .product-item', timeout=5000)
            except: pass
            # Wait for response handlers to complete processing
            await asyncio.sleep(2)
            
            # Fallback: scrape from DOM if no API results
            if not results:
                cards = await page.query_selector_all('li[data-test="product-card"], .product-card, .product-item')
                for card in cards:
                    try:
                        name_el = await card.query_selector('[data-test="product-title"], .product-title, h3, h2')
                        name = await name_el.inner_text() if name_el else ""
                        price_el = await card.query_selector('[data-test="price"], .price')
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
                        logger.debug(f"Error parsing Delhaize product from DOM: {e}")
        except Exception as e:
            logger.warning(f"Delhaize navigation error: {e}")
        await browser.close()
    
    # Filter results to match search term (case-insensitive partial match)
    search_lower = search_term.lower()
    filtered_results = [r for r in results if r.get('name') and search_lower in r['name'].lower()]
    return filtered_results
