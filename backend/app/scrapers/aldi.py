from playwright.async_api import async_playwright
import urllib.parse

async def scrape_aldi(search_term: str):
    results = []
    print(f"🛒 Aldi: Scanning...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(10000)  # 10 second default timeout
        safe_term = urllib.parse.quote(search_term)
        url = f"https://www.aldi.be/nl/zoekresultaten.html?query={safe_term}&searchCategory=Submitted%20Search"
        try:
            await page.goto(url, timeout=12000)
            try: await page.click('#onetrust-accept-btn-handler', timeout=2000)
            except: pass
            await page.wait_for_selector('.mod-article-tile', timeout=5000)
            products = await page.query_selector_all('.mod-article-tile')
            for p in products:
                try:
                    name_el = await p.query_selector('.mod-article-tile__title')
                    name = await name_el.inner_text()
                    price_wrapper = await p.query_selector('.price__wrapper')
                    if price_wrapper:
                        price_text = await price_wrapper.inner_text()
                        price_clean = price_text.replace('\n', '').replace('€', '').replace(',', '.').strip()
                        price = float(price_clean)
                    else:
                        price = 0.0
                    img_el = await p.query_selector('img')
                    img_src = await img_el.get_attribute('src') if img_el else ""
                    # Ensure image URL is complete
                    if img_src and not img_src.startswith('http'):
                        img_src = f"https://www.aldi.be{img_src}"
                    link_el = await p.query_selector('a')
                    link_href = await link_el.get_attribute('href') if link_el else ""
                    if link_href and not link_href.startswith('http'):
                        link_href = f"https://www.aldi.be{link_href}"
                    results.append({"store": "Aldi", "name": name.strip(), "price": price, "volume": "", "image": img_src, "link": link_href})
                except: pass
        except: pass
        await browser.close()
    return results
