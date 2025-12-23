from playwright.async_api import async_playwright
import urllib.parse

async def scrape_prikentik(search_term: str):
    results = []
    print(f"🍺 Prik&Tik: Scanning...")
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            safe_term = urllib.parse.quote(search_term)
            await page.goto(f"https://www.prikentik.be/catalogsearch/result/?q={safe_term}", timeout=15000)
            try:
                accept_btn = await page.wait_for_selector('#onetrust-accept-btn-handler', timeout=4000)
                await accept_btn.click()
            except: pass
            try: await page.wait_for_selector('.product-item', timeout=8000)
            except: pass
            products = await page.query_selector_all('.product-item')
            for prod in products:
                try:
                    name_el = await prod.query_selector('.product-item-link')
                    name = await name_el.inner_text()
                    price_el = await prod.query_selector('.price')
                    price_text = await price_el.inner_text()
                    price = float(price_text.replace('€', '').replace(',', '.').strip())
                    link = await name_el.get_attribute('href')
                    img_el = await prod.query_selector('.product-image-photo')
                    img = await img_el.get_attribute('src') if img_el else ""
                    results.append({"store": "Prik&Tik", "name": name.strip(), "price": price, "volume": "", "image": img, "link": link})
                except: pass
            await browser.close()
        except: pass
    return results
