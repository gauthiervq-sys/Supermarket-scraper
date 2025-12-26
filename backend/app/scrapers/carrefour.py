from playwright.async_api import async_playwright
import urllib.parse

# Default page timeout in milliseconds
DEFAULT_PAGE_TIMEOUT = 10000

async def scrape_carrefour(search_term: str):
    results = []
    print(f"🟠 Carrefour: Scanning...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        page = await browser.new_page()
        page.set_default_timeout(DEFAULT_PAGE_TIMEOUT)
        safe_term = urllib.parse.quote(search_term)
        try:
            await page.goto(f"https://www.carrefour.be/nl/search?q={safe_term}", timeout=12000)
            try:
                accept_btn = await page.wait_for_selector('#onetrust-accept-btn-handler', timeout=2000)
                await accept_btn.click()
            except: pass
            await page.wait_for_selector('.product-card', timeout=6000)
            cards = await page.query_selector_all('.product-card')
            for card in cards:
                try:
                    name_el = await card.query_selector('.product-card__title')
                    name = await name_el.inner_text() if name_el else "Naamloos"
                    price_el = await card.query_selector('.product-card-price__price')
                    if price_el:
                        price_txt = await price_el.inner_text()
                        price = float(price_txt.replace('\n', '').replace('€', '').replace(',', '.').strip())
                    else:
                        price = 0.0
                    link_el = await card.query_selector('a.product-card__title-link')
                    link_href = await link_el.get_attribute('href') if link_el else ""
                    if link_href and not link_href.startswith('http'):
                        link_href = f"https://www.carrefour.be{link_href}"
                    img_el = await card.query_selector('img')
                    img = await img_el.get_attribute('src') if img_el else ""
                    # Ensure image URL is complete
                    if img and not img.startswith('http'):
                        img = f"https://www.carrefour.be{img}"
                    results.append({"store": "Carrefour", "name": name.strip(), "price": price, "volume": "", "image": img, "link": link_href})
                except: pass
        except: pass
        await browser.close()
    return results
