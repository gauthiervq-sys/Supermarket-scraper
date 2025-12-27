from playwright.async_api import async_playwright
import urllib.parse
import asyncio
import logging

# Default page timeout in milliseconds
DEFAULT_PAGE_TIMEOUT = 10000
logger = logging.getLogger(__name__)

async def scrape_ah(search_term: str):
    results = []
    print(f"🛒 AH: Scanning...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()
        page.set_default_timeout(DEFAULT_PAGE_TIMEOUT)
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        async def handle_response(response):
            url_lower = response.url.lower()
            if response.status == 200 and any(x in url_lower for x in ["search", "product", "zoeken"]):
                try:
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        data = await response.json()
                        # Handle different API response structures
                        cards = data.get('cards', [])
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
                                    logger.debug(f"Error parsing AH product: {e}")
                        
                        # Also check for products array directly
                        products = data.get('products', [])
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
                                logger.debug(f"Error parsing AH product: {e}")
                except Exception as e:
                    logger.debug(f"Error parsing AH response: {e}")
        
        page.on("response", handle_response)
        safe_term = urllib.parse.quote(search_term)
        try:
            await page.goto(f"https://www.ah.be/zoeken?query={safe_term}", timeout=12000)
            try: await page.click('#accept-cookies', timeout=2000)
            except: pass
            # Wait for products to load with multiple selectors
            try:
                await page.wait_for_selector('article[data-test-id="product-card"], .product-card, [data-testid="product"]', timeout=5000)
            except: pass
            # Wait for response handlers to complete processing
            await asyncio.sleep(2)
        except Exception as e:
            logger.warning(f"AH navigation error: {e}")
        await browser.close()
    
    # Filter results to match search term (case-insensitive partial match)
    search_lower = search_term.lower()
    filtered_results = [r for r in results if r.get('name') and search_lower in r['name'].lower()]
    return filtered_results
