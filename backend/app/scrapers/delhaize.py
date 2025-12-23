from playwright.async_api import async_playwright
import urllib.parse

async def scrape_delhaize(search_term: str):
    results = []
    print(f"🦁 Delhaize: Scanning...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
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
                        results.append({"store": "Delhaize", "name": name, "price": float(price), "volume": item.get('measurementUnit', ''), "image": img, "link": link})
                except: pass
        page.on("response", handle_response)
        safe_term = urllib.parse.quote(search_term)
        try:
            await page.goto(f"https://www.delhaize.be/nl/shop/search?q={safe_term}")
            try: await page.wait_for_selector('#onetrust-accept-btn-handler', timeout=4000).click()
            except: pass
            await page.wait_for_selector('li[data-test="product-card"]', timeout=10000)
        except: pass
        await browser.close()
    return results
