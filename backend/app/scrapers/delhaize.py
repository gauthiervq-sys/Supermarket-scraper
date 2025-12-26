from playwright.async_api import async_playwright
import urllib.parse
import asyncio

# Default page timeout in milliseconds
DEFAULT_PAGE_TIMEOUT = 10000

async def scrape_delhaize(search_term: str):
    results = []
    print(f"🦁 Delhaize: Scanning...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(DEFAULT_PAGE_TIMEOUT)
        async def handle_response(response):
            if "search" in response.url and response.status == 200:
                try:
                    data = await response.json()
                    items = data.get('products', []) or data.get('results', [])
                    for item in items:
                        name = item.get('name', 'Naamloos')
                        price = item.get('price', {}).get('value', 0.0)
                        code = item.get('code', '')
                        link = f"https://www.delhaize.be/nl/shop/p/{code}" if code else ""
                        img = item.get('images', [{}])[0].get('url', '') if item.get('images') else ""
                        # Ensure image URL is complete
                        if img and not img.startswith('http'):
                            img = f"https://www.delhaize.be{img}"
                        results.append({"store": "Delhaize", "name": name, "price": float(price), "volume": item.get('measurementUnit', ''), "image": img, "link": link})
                except: pass
        page.on("response", handle_response)
        safe_term = urllib.parse.quote(search_term)
        try:
            await page.goto(f"https://www.delhaize.be/nl/shop/search?q={safe_term}", timeout=12000)
            try:
                accept_btn = await page.wait_for_selector('#onetrust-accept-btn-handler', timeout=2000)
                await accept_btn.click()
            except: pass
            await page.wait_for_selector('li[data-test="product-card"]', timeout=5000)
            # Wait for response handlers to complete processing
            await asyncio.sleep(2)
        except: pass
        await browser.close()
    
    # Filter results to match search term
    search_lower = search_term.lower()
    filtered_results = [r for r in results if search_lower in r['name'].lower()]
    return filtered_results
