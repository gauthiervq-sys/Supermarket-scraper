from playwright.async_api import async_playwright
import urllib.parse

async def scrape_ah(search_term: str):
    results = []
    print(f"🛒 AH: Scanning...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()
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
            await page.goto(f"https://www.ah.be/zoeken?query={safe_term}")
            try: await page.click('#accept-cookies', timeout=3000)
            except: pass
            await page.wait_for_selector('article[data-test-id="product-card"]', timeout=8000)
        except: pass
        await browser.close()
    return results
