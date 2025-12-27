from playwright.async_api import async_playwright
import urllib.parse
import logging
import os

# Default page timeout in milliseconds
DEFAULT_PAGE_TIMEOUT = 10000
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
logger = logging.getLogger(__name__)

async def scrape_woocommerce(store_name, base_url, search_term):
    results = []
    safe_term = urllib.parse.quote(search_term)
    url = f"{base_url}?s={safe_term}&post_type=product"
    
    logger.info(f"📦 {store_name}: Checking {url}")
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            page.set_default_timeout(DEFAULT_PAGE_TIMEOUT)
            await page.goto(url, timeout=15000)
            try:
                await page.wait_for_selector('.product', timeout=6000)
                if DEBUG_MODE:
                    logger.debug(f"  {store_name}: Products loaded on page")
            except:
                if DEBUG_MODE:
                    logger.debug(f"  {store_name}: No product elements found on page")
            products = await page.query_selector_all('.product')
            if DEBUG_MODE:
                logger.debug(f"  {store_name}: Found {len(products)} product elements on page")
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
                except Exception as e:
                    if DEBUG_MODE:
                        logger.debug(f"  {store_name}: Error parsing product: {e}")
            await browser.close()
        except Exception as e:
            logger.warning(f"  {store_name}: Scraping error: {e}")
    
    # Filter results to match search term
    search_lower = search_term.lower()
    if DEBUG_MODE:
        logger.debug(f"  {store_name}: Found {len(results)} total results before filtering")
    filtered_results = [r for r in results if search_lower in r['name'].lower()]
    if DEBUG_MODE and len(results) != len(filtered_results):
        logger.debug(f"  {store_name}: Filtered to {len(filtered_results)} results matching '{search_term}'")
    
    return filtered_results

async def scrape_snuffelstore(q): return await scrape_woocommerce("Snuffelstore", "https://www.snuffelstore.be/", q)
async def scrape_drinkscorner(q): return await scrape_woocommerce("Drinks Corner", "https://drinkscorner.be/", q)
