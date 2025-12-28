from playwright.async_api import async_playwright
import urllib.parse
import logging
import os
import re

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
        context = await browser.new_context()
        page = await context.new_page()
        page.set_default_timeout(DEFAULT_PAGE_TIMEOUT)
        
        try:
            await page.goto(url, timeout=15000, wait_until="networkidle")
            if DEBUG_MODE:
                logger.debug(f"  Aldi: Page loaded, waiting for content")
            
            try:
                await page.click('#onetrust-accept-btn-handler', timeout=2000)
                if DEBUG_MODE:
                    logger.debug(f"  Aldi: Accepted cookies")
            except: pass
            
            await page.wait_for_selector('.mod-article-tile', timeout=6000)
            products = await page.query_selector_all('.mod-article-tile')
            if DEBUG_MODE:
                logger.debug(f"  Aldi: Found {len(products)} product tiles on search page")
            
            # Collect product links from search results
            product_links = []
            for p in products:
                try:
                    link_el = await p.query_selector('a')
                    link_href = await link_el.get_attribute('href') if link_el else ""
                    if link_href:
                        if not link_href.startswith('http'):
                            link_href = f"https://www.aldi.be{link_href}"
                        product_links.append(link_href)
                except Exception as e:
                    if DEBUG_MODE:
                        logger.debug(f"  Aldi: Error extracting link: {e}")
            
            if DEBUG_MODE:
                logger.debug(f"  Aldi: Collected {len(product_links)} product links, visiting each...")
            
            # Visit each product page to extract detailed information
            for idx, product_url in enumerate(product_links):
                try:
                    detail_page = await context.new_page()
                    detail_page.set_default_timeout(DEFAULT_PAGE_TIMEOUT)
                    
                    await detail_page.goto(product_url, timeout=15000, wait_until="domcontentloaded")
                    
                    # Extract product name
                    name = ""
                    name_el = await detail_page.query_selector('h1, .product-title, .mod-article-tile__title')
                    if name_el:
                        name = await name_el.inner_text()
                    
                    # Extract price from detail page
                    price = 0.0
                    price_wrapper = await detail_page.query_selector('.price__wrapper, .price, [class*="price"]')
                    if price_wrapper:
                        price_text = await price_wrapper.inner_text()
                        price_clean = price_text.replace('\n', '').replace('€', '').replace(',', '.').strip()
                        try:
                            # Extract just the numeric value
                            import re
                            price_match = re.search(r'(\d+[.,]\d+|\d+)', price_clean)
                            if price_match:
                                price = float(price_match.group(1).replace(',', '.'))
                        except:
                            price = 0.0
                    
                    # Extract volume/quantity
                    volume = ""
                    quantity_el = await detail_page.query_selector('.mod-article-tile__quantity, .product-quantity, [class*="quantity"]')
                    if quantity_el:
                        volume = await quantity_el.inner_text()
                    if not volume:
                        subtitle_el = await detail_page.query_selector('.mod-article-tile__subtitle, .product-subtitle')
                        if subtitle_el:
                            volume = await subtitle_el.inner_text()
                    
                    # Extract image
                    img_src = ""
                    img_el = await detail_page.query_selector('img.product-image, .product-image img, img')
                    if img_el:
                        img_src = await img_el.get_attribute('src') or ""
                        if img_src and not img_src.startswith('http'):
                            img_src = f"https://www.aldi.be{img_src}"
                    
                    if name:  # Only add if we got a name
                        results.append({
                            "store": "Aldi",
                            "name": name.strip(),
                            "price": price,
                            "volume": volume.strip(),
                            "image": img_src,
                            "link": product_url
                        })
                        
                        if DEBUG_MODE:
                            logger.debug(f"  Aldi: [{idx+1}/{len(product_links)}] Extracted: {name[:50]} - €{price}")
                    
                    await detail_page.close()
                    
                except Exception as e:
                    if DEBUG_MODE:
                        logger.debug(f"  Aldi: Error scraping product page {product_url}: {e}")
                    try:
                        await detail_page.close()
                    except:
                        pass
                        
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
