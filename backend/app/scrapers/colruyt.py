from playwright.async_api import async_playwright
import urllib.parse

async def scrape_colruyt(search_term: str):
    results = []
    print(f"🛒 Colruyt: Scanning...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        page = await browser.new_page()
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
                        results.append({
                            "store": "Colruyt",
                            "name": item.get('name'),
                            "price": float(price),
                            "volume": item.get('content', ''),
                            "image": item.get('fullImage', ''),
                            "link": link
                        })
                except: pass
        page.on("response", handle_response)
        safe_term = urllib.parse.quote(search_term)
        await page.goto(f"https://www.collectandgo.be/nl/zoek?searchTerm={safe_term}")
        try:
            try:
                accept_btn = await page.wait_for_selector('#onetrust-accept-btn-handler', timeout=3000)
                await accept_btn.click()
            except: pass
            await page.wait_for_selector('.product-card', timeout=8000)
        except: pass
        await browser.close()
    return results
