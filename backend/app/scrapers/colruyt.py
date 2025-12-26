from playwright.async_api import async_playwright
import urllib.parse
import asyncio
import logging

# Default page timeout in milliseconds
DEFAULT_PAGE_TIMEOUT = 10000
logger = logging.getLogger(__name__)

async def scrape_colruyt(search_term: str):
    results = []
    print(f"🛒 Colruyt: Scanning...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        page.set_default_timeout(DEFAULT_PAGE_TIMEOUT)
        
        async def handle_response(response):
            # Look for various API endpoints that might contain product data
            url_lower = response.url.lower()
            if response.status == 200 and any(x in url_lower for x in ["productview", "search", "product"]):
                try:
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        data = await response.json()
                        # Handle different API response structures
                        products = data.get('catalogEntryView', []) or data.get('products', []) or data.get('items', [])
                        for item in products:
                            try:
                                price_data = item.get('price', [])
                                if isinstance(price_data, list) and price_data:
                                    price = price_data[0].get('offerPrice', 0.0)
                                elif isinstance(price_data, dict):
                                    price = price_data.get('offerPrice', price_data.get('value', 0.0))
                                else:
                                    price = item.get('price', 0.0)
                                
                                prod_id = item.get('uniqueID', item.get('id', ''))
                                link = f"https://www.collectandgo.be/site/nl/artikel-detail/{prod_id}"
                                img_url = item.get('fullImage', item.get('image', ''))
                                # Ensure image URL is complete
                                if img_url and not img_url.startswith('http'):
                                    img_url = f"https://www.collectandgo.be{img_url}"
                                
                                name = item.get('name', item.get('title', ''))
                                if name:  # Only add if we have a name
                                    results.append({
                                        "store": "Colruyt",
                                        "name": name,
                                        "price": float(price) if price else 0.0,
                                        "volume": item.get('content', item.get('volume', '')),
                                        "image": img_url,
                                        "link": link
                                    })
                            except Exception as e:
                                logger.debug(f"Error parsing Colruyt product: {e}")
                except Exception as e:
                    logger.debug(f"Error parsing Colruyt response: {e}")
        
        page.on("response", handle_response)
        safe_term = urllib.parse.quote(search_term)
        try:
            await page.goto(f"https://www.collectandgo.be/nl/zoek?searchTerm={safe_term}", timeout=12000)
            try:
                accept_btn = await page.wait_for_selector('#onetrust-accept-btn-handler', timeout=2000)
                await accept_btn.click()
            except: pass
            # Wait for products to load
            try:
                await page.wait_for_selector('.product-card, .product-item, [data-testid="product"]', timeout=5000)
            except: pass
            # Wait for response handlers to complete processing
            await asyncio.sleep(2)
        except Exception as e:
            logger.warning(f"Colruyt navigation error: {e}")
        await browser.close()
    
    # Filter results to match search term (case-insensitive partial match)
    search_lower = search_term.lower()
    filtered_results = [r for r in results if r.get('name') and search_lower in r['name'].lower()]
    return filtered_results
