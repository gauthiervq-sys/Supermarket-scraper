from playwright.async_api import async_playwright
import urllib.parse

async def scrape_woocommerce(store_name, base_url, search_term):
    results = []
    print(f"📦 {store_name}: Scanning...")
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            page.set_default_timeout(10000)  # 10 second default timeout
            safe_term = urllib.parse.quote(search_term)
            await page.goto(f"{base_url}?s={safe_term}&post_type=product", timeout=15000)
            try: await page.wait_for_selector('.product', timeout=6000)
            except: pass
            products = await page.query_selector_all('.product')
            for prod in products:
                try:
                    title_el = await prod.query_selector('.woocommerce-loop-product__title, .product-title, h3')
                    name = await title_el.inner_text() if title_el else "Naamloos"
                    price_el = await prod.query_selector('span.price bdi')
                    price_txt = await price_el.inner_text() if price_el else "0"
                    price = float(price_txt.replace('€', '').replace(',', '.').replace('&nbsp;', '').strip())
                    link_el = await prod.query_selector('a')
                    link = await link_el.get_attribute('href') if link_el else ""
                    img_el = await prod.query_selector('img')
                    img = await img_el.get_attribute('src') if img_el else ""
                    # Ensure image URL is complete
                    if img and not img.startswith('http'):
                        img = f"{base_url.rstrip('/')}{img}" if img.startswith('/') else f"{base_url}{img}"
                    results.append({"store": store_name, "name": name.strip(), "price": price, "volume": "", "image": img, "link": link})
                except: pass
            await browser.close()
        except: pass
    return results

async def scrape_snuffelstore(q): return await scrape_woocommerce("Snuffelstore", "https://www.snuffelstore.be/", q)
async def scrape_drinkscorner(q): return await scrape_woocommerce("Drinks Corner", "https://drinkscorner.be/", q)
