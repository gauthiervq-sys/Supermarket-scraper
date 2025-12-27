from playwright.async_api import async_playwright
import urllib.parse
import asyncio
import logging

# Default page timeout in milliseconds
DEFAULT_PAGE_TIMEOUT = 10000
logger = logging.getLogger(__name__)

async def scrape_prikentik(search_term: str):
    results = []
    print(f"🍺 Prik&Tik: Scanning...")
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            page.set_default_timeout(DEFAULT_PAGE_TIMEOUT)
            safe_term = urllib.parse.quote(search_term)
            await page.goto(f"https://www.prikentik.be/catalogsearch/result/?q={safe_term}", timeout=12000)
            try:
                accept_btn = await page.wait_for_selector('#onetrust-accept-btn-handler, .cookie-accept', timeout=2000)
                await accept_btn.click()
            except: pass
            
            # Wait for products to load
            try: 
                await page.wait_for_selector('.product-item, .product-items', timeout=5000)
            except: pass
            
            # Allow lazy loading to complete
            await asyncio.sleep(1)
            
            # Scroll to trigger lazy loading
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
            
            products = await page.query_selector_all('.product-item, li.product-item')
            for prod in products:
                try:
                    name_el = await prod.query_selector('.product-item-link, .product-name a, a.product-item-link')
                    name = await name_el.inner_text() if name_el else ""
                    if not name:
                        continue
                        
                    price_el = await prod.query_selector('.price, .price-wrapper .price')
                    price = 0.0
                    if price_el:
                        price_text = await price_el.inner_text()
                        price = float(price_text.replace('€', '').replace(',', '.').strip())
                    
                    link = await name_el.get_attribute('href') if name_el else ""
                    
                    # Try multiple image selectors and attributes for lazy loading
                    img_el = await prod.query_selector('.product-image-photo, img.photo, .product-item-photo img')
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
                    logger.debug(f"Error parsing Prik&Tik product: {e}")
            await browser.close()
        except Exception as e:
            logger.warning(f"Prik&Tik scraping error: {e}")
    
    # Filter results to match search term (case-insensitive partial match)
    search_lower = search_term.lower()
    filtered_results = [r for r in results if r.get('name') and search_lower in r['name'].lower()]
    return filtered_results
