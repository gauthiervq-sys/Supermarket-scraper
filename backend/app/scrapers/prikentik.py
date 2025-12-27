from playwright.async_api import async_playwright
import urllib.parse
import asyncio
import logging
import os
from app.ocr_utils import try_ocr_price_extraction

# Default page timeout in milliseconds
DEFAULT_PAGE_TIMEOUT = 10000
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
logger = logging.getLogger(__name__)

async def scrape_prikentik(search_term: str):
    results = []
    safe_term = urllib.parse.quote(search_term)
    url = f"https://www.prikentik.be/catalogsearch/result/?q={safe_term}"
    
    logger.info(f"🍺 Prik&Tik: Checking {url}")
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            page.set_default_timeout(DEFAULT_PAGE_TIMEOUT)
            await page.goto(url, timeout=15000, wait_until="networkidle")
            if DEBUG_MODE:
                logger.debug(f"  Prik&Tik: Page loaded, waiting for content")
            
            try:
                accept_btn = await page.wait_for_selector('#onetrust-accept-btn-handler, .cookie-accept', timeout=2000)
                await accept_btn.click()
                await asyncio.sleep(0.5)
                if DEBUG_MODE:
                    logger.debug(f"  Prik&Tik: Accepted cookies")
            except: pass
            
            # Wait for products to load
            try: 
                await page.wait_for_selector('.product-item, .product-items, .products-grid', timeout=6000)
                if DEBUG_MODE:
                    logger.debug(f"  Prik&Tik: Products loaded on page")
            except:
                if DEBUG_MODE:
                    logger.debug(f"  Prik&Tik: No product elements found on page")
            
            # Scroll to trigger lazy loading
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await asyncio.sleep(1)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
            
            # Additional wait for lazy loading to complete
            await asyncio.sleep(2)
            
            products = await page.query_selector_all('.product-item, li.product-item, .item.product')
            if DEBUG_MODE:
                logger.debug(f"  Prik&Tik: Found {len(products)} product elements on page")
            for prod in products:
                try:
                    name_el = await prod.query_selector('.product-item-link, .product-name a, a.product-item-link, .product-item-name a')
                    name = await name_el.inner_text() if name_el else ""
                    if not name:
                        continue
                        
                    price_el = await prod.query_selector('.price, .price-wrapper .price, [data-price-type="finalPrice"]')
                    price = 0.0
                    if price_el:
                        try:
                            price_text = await price_el.inner_text()
                            if price_text and price_text.strip():
                                price = float(price_text.replace('€', '').replace(',', '.').strip())
                            else:
                                # If no text, price might be in an image - try OCR
                                if DEBUG_MODE:
                                    logger.debug(f"  Prik&Tik: No price text found, trying OCR for '{name}'")
                                ocr_price = await try_ocr_price_extraction(page, price_el)
                                if ocr_price:
                                    price = ocr_price
                                    if DEBUG_MODE:
                                        logger.debug(f"  Prik&Tik: OCR extracted price: €{price}")
                        except (ValueError, AttributeError) as e:
                            # Price parsing failed, try OCR
                            if DEBUG_MODE:
                                logger.debug(f"  Prik&Tik: Price parsing failed for '{name}', trying OCR: {e}")
                            ocr_price = await try_ocr_price_extraction(page, price_el)
                            if ocr_price:
                                price = ocr_price
                                if DEBUG_MODE:
                                    logger.debug(f"  Prik&Tik: OCR extracted price: €{price}")
                    
                    link = await name_el.get_attribute('href') if name_el else ""
                    
                    # Try multiple image selectors and attributes for lazy loading
                    img_el = await prod.query_selector('.product-image-photo, img.photo, .product-item-photo img, img')
                    img = ""
                    if img_el:
                        # Try various lazy loading attributes first, breaking early when found
                        for attr in ['data-original', 'data-src', 'data-lazy', 'data-amsrc', 'srcset', 'src']:
                            img = await img_el.get_attribute(attr)
                            if img:
                                break
                        
                        # If srcset, take the first URL
                        if img and ' ' in img:
                            img = img.split()[0]
                    
                    # Ensure image URL is complete
                    if img and not img.startswith('http'):
                        if img.startswith('//'):
                            img = f"https:{img}"
                        else:
                            img = f"https://www.prikentik.be{img}"
                    
                    results.append({
                        "store": "Prik&Tik",
                        "name": name.strip(),
                        "price": price,
                        "volume": "",
                        "image": img,
                        "link": link
                    })
                except Exception as e:
                    if DEBUG_MODE:
                        logger.debug(f"  Prik&Tik: Error parsing product: {e}")
            await browser.close()
        except Exception as e:
            logger.warning(f"  Prik&Tik: Scraping error: {e}")
    
    # Filter results to match search term (case-insensitive partial match)
    search_lower = search_term.lower()
    if DEBUG_MODE:
        logger.debug(f"  Prik&Tik: Found {len(results)} total results before filtering")
    filtered_results = [r for r in results if r.get('name') and search_lower in r['name'].lower()]
    if DEBUG_MODE and len(results) != len(filtered_results):
        logger.debug(f"  Prik&Tik: Filtered to {len(filtered_results)} results matching '{search_term}'")
    
    return filtered_results
