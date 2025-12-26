from playwright.async_api import async_playwright
import urllib.parse

# Default page timeout in milliseconds
DEFAULT_PAGE_TIMEOUT = 10000

async def scrape_lidl(search_term: str):
    results = []
    print(f"🟡 Lidl: Scanning...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(DEFAULT_PAGE_TIMEOUT)
        async def handle_response(response):
            if "search" in response.url and "api" in response.url and response.status == 200:
                try:
                    data = await response.json()
                    prods = data.get('results', []) or data.get('products', [])
                    for item in prods:
                        name = item.get('keyfacts', {}).get('title', '') or item.get('fullTitle', '')
                        price = item.get('price', {}).get('price', 0.0)
                        img = item.get('image', '')
                        # Ensure image URL is complete
                        if img and not img.startswith('http'):
                            img = f"https://www.lidl.be{img}"
                        prod_id = item.get('productId', '')
                        link = f"https://www.lidl.be/p/{prod_id}" if prod_id else f"https://www.lidl.be/q/nl-BE/search?q={search_term}"
                        results.append({"store": "Lidl", "name": name, "price": float(price) if isinstance(price, (int, float)) else 0.0, "volume": "", "image": img, "link": link})
                except: pass
        page.on("response", handle_response)
        safe_term = urllib.parse.quote(search_term)
        try:
            await page.goto(f"https://www.lidl.be/q/nl-BE/search?q={safe_term}", timeout=12000)
            try:
                accept_btn = await page.wait_for_selector('#onetrust-accept-btn-handler', timeout=2000)
                await accept_btn.click()
            except: pass
            await page.wait_for_selector('article', timeout=5000)
        except: pass
        await browser.close()
    return results
