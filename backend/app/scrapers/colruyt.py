from playwright.async_api import async_playwright
import urllib.parse
import asyncio

# Default page timeout in milliseconds
DEFAULT_PAGE_TIMEOUT = 10000

async def scrape_colruyt(search_term: str):
    results = []
    print(f"🛒 Colruyt: Scanning...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        page = await browser.new_page()
        page.set_default_timeout(DEFAULT_PAGE_TIMEOUT)
        async def handle_response(response):
            if "productview" in response.url and response.status == 200:
                try:
                    data = await response.json()
                    products = data.get('catalogEntryView', [])
                    for item in products:
                        price_data = item.get('price', [])
                        price = price_data[0].get('offerPrice', 0.0) if price_data else 0.0
                        prod_id = item.get('uniqueID', '')
                        link = f"https://www.collectandgo.be/site/nl/artikel-detail/{prod_id}"
                        img_url = item.get('fullImage', '')
                        # Ensure image URL is complete
                        if img_url and not img_url.startswith('http'):
                            img_url = f"https://www.collectandgo.be{img_url}"
                        results.append({
                            "store": "Colruyt",
                            "name": item.get('name'),
                            "price": float(price),
                            "volume": item.get('content', ''),
                            "image": img_url,
                            "link": link
                        })
                except: pass
        page.on("response", handle_response)
        safe_term = urllib.parse.quote(search_term)
        try:
            await page.goto(f"https://www.collectandgo.be/nl/zoek?searchTerm={safe_term}", timeout=12000)
            try:
                accept_btn = await page.wait_for_selector('#onetrust-accept-btn-handler', timeout=2000)
                await accept_btn.click()
            except: pass
            await page.wait_for_selector('.product-card', timeout=5000)
            # Wait for response handlers to complete processing
            await asyncio.sleep(2)
        except: pass
        await browser.close()
    
    # Filter results to match search term
    search_lower = search_term.lower()
    filtered_results = [r for r in results if search_lower in r['name'].lower()]
    return filtered_results
