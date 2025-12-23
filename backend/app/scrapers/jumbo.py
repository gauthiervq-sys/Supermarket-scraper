import httpx
import urllib.parse

async def scrape_jumbo(search_term: str):
    results = []
    print(f"🐘 Jumbo: Scanning (API)...")
    headers = {"User-Agent": "Jumbo/7.5.0 (Android)", "x-jumbo-unique-id": "android-device-123"}
    url = "https://mobileapi.jumbo.com/v17/search"
    params = {"q": search_term, "offset": 0, "limit": 15}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, params=params, timeout=10.0)
            data = resp.json()
            items = data.get('products', {}).get('data', [])
            for p in items:
                price_cent = p.get('prices', {}).get('price', {}).get('amount', 0)
                price = price_cent / 100 if price_cent else 0.0
                imgs = p.get('imageInfo', {}).get('primaryView', [])
                img = imgs[0].get('url', '') if imgs else ""
                prod_id = p.get('id', '')
                title_slug = p.get('title', '').replace(' ', '-')
                link = f"https://www.jumbo.com/producten/{title_slug}-{prod_id}"
                results.append({"store": "Jumbo", "name": p.get('title'), "price": float(price), "volume": p.get('quantity', ''), "image": img, "link": link})
    except Exception as e: print(f"Jumbo error: {e}")
    return results
