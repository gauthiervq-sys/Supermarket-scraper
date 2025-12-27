from playwright.async_api import async_playwright
import urllib.parse
import logging
import os

# Default page timeout in milliseconds
DEFAULT_PAGE_TIMEOUT = 10000
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
logger = logging.getLogger(__name__)

async def scrape_aldi(search_term: str):
    results = []
    safe_term = urllib.parse.quote(search_term)
    url = f"https://www.aldi.be/nl/zoekresultaten.html?query={safe_term}&searchCategory=Submitted%20Search"
    
    logger.info(f"🛒 Aldi: Checking {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(DEFAULT_PAGE_TIMEOUT)
        try:
            await page.goto(url, timeout=12000)
            try:
                await page.click('#onetrust-accept-btn-handler', timeout=2000)
                if DEBUG_MODE:
                    logger.debug(f"  Aldi: Accepted cookies")
            except: pass
            await page.wait_for_selector('.mod-article-tile', timeout=5000)
            products = await page.query_selector_all('.mod-article-tile')
            if DEBUG_MODE:
                logger.debug(f"  Aldi: Found {len(products)} product elements on page")
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
                    
                    # Try to extract volume from various possible locations
                    volume = ""
                    quantity_el = await p.query_selector('.mod-article-tile__quantity')
                    if quantity_el:
                        volume = await quantity_el.inner_text()
                    if not volume:
                        subtitle_el = await p.query_selector('.mod-article-tile__subtitle')
                        if subtitle_el:
                            volume = await subtitle_el.inner_text()
                    if not volume:
                        subtitle_attr = await p.get_attribute('data-subtitle')
                        if subtitle_attr:
                            volume = subtitle_attr
                    
                    img_el = await p.query_selector('img')
                    img_src = await img_el.get_attribute('src') if img_el else ""
                    # Ensure image URL is complete
                    if img_src and not img_src.startswith('http'):
                        img_src = f"https://www.aldi.be{img_src}"
                    link_el = await p.query_selector('a')
                    link_href = await link_el.get_attribute('href') if link_el else ""
                    if link_href and not link_href.startswith('http'):
                        link_href = f"https://www.aldi.be{link_href}"
                    results.append({"store": "Aldi", "name": name.strip(), "price": price, "volume": volume.strip(), "image": img_src, "link": link_href})
                except Exception as e:
                    if DEBUG_MODE:
                        logger.debug(f"  Aldi: Error parsing product: {e}")
        except Exception as e:
            logger.warning(f"  Aldi: Navigation error: {e}")
        await browser.close()
    
    # Filter results to match search term
    search_lower = search_term.lower()
    if DEBUG_MODE:
        logger.debug(f"  Aldi: Found {len(results)} total results before filtering")
    filtered_results = [r for r in results if search_lower in r['name'].lower()]
    if DEBUG_MODE and len(results) != len(filtered_results):
        logger.debug(f"  Aldi: Filtered to {len(filtered_results)} results matching '{search_term}'")
    
    return filtered_results
