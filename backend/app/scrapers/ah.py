from playwright.async_api import async_playwright
import urllib.parse
import asyncio

# Default page timeout in milliseconds
DEFAULT_PAGE_TIMEOUT = 10000

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
            if "search" in response.url and response.status == 200:
                try:
                    data = await response.json()
                    cards = data.get('cards', [])
                    for card in cards:
                        for prod in card.get('products', []):
                            images = prod.get('images', [])
                            img_url = images[0].get('url') if images else ""
                            # Ensure image URL is complete
                            if img_url and not img_url.startswith('http'):
                                img_url = f"https://www.ah.be{img_url}"
                            link_slug = prod.get('link', '')
                            full_link = f"https://www.ah.be{link_slug}"
                            results.append({
                                "store": "Albert Heijn",
                                "name": prod.get('title'),
                                "price": float(prod.get('price', {}).get('now', 0.0)),
                                "volume": prod.get('price', {}).get('unitSize', ''),
                                "image": img_url,
                                "link": full_link
                            })
                except: pass
        page.on("response", handle_response)
        safe_term = urllib.parse.quote(search_term)
        try:
            await page.goto(f"https://www.ah.be/zoeken?query={safe_term}", timeout=12000)
            try: await page.click('#accept-cookies', timeout=2000)
            except: pass
            await page.wait_for_selector('article[data-test-id="product-card"]', timeout=5000)
            # Wait for response handlers to complete processing
            await asyncio.sleep(2)
        except: pass
        await browser.close()
    
    # Filter results to match search term
    search_lower = search_term.lower()
    filtered_results = [r for r in results if search_lower in r['name'].lower()]
    return filtered_results
