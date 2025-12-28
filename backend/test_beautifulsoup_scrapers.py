#!/usr/bin/env python3
"""
Test script to verify BeautifulSoup-based scrapers.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.scrapers.aldi import scrape_aldi
from app.scrapers.prikentik import scrape_prikentik
from app.scrapers.carrefour import scrape_carrefour
from app.scrapers.small_shops import scrape_snuffelstore, scrape_drinkscorner
from app.scrapers.colruyt import scrape_colruyt
from app.scrapers.ah import scrape_ah
from app.scrapers.delhaize import scrape_delhaize
from app.scrapers.lidl import scrape_lidl
from app.scrapers.jumbo import scrape_jumbo

async def test_scraper(name, scraper_func, search_term="cola"):
    """Test a single scraper."""
    print(f"\n{'='*60}")
    print(f"Testing {name}")
    print(f"{'='*60}")
    
    try:
        results = await scraper_func(search_term)
        print(f"✅ {name} completed successfully")
        print(f"   Found {len(results)} products")
        if results:
            sample = results[0]
            print(f"   Sample: {sample['name'][:50]} - €{sample['price']}")
        return len(results)
    except Exception as e:
        print(f"❌ {name} failed: {e}")
        import traceback
        traceback.print_exc()
        return 0

async def main():
    """Run all scraper tests."""
    print("\n🚀 Starting BeautifulSoup Scraper Tests")
    print("Testing all scrapers with search term 'cola'")
    
    scrapers = [
        ("Aldi", scrape_aldi),
        ("Prik&Tik", scrape_prikentik),
        ("Carrefour", scrape_carrefour),
        ("Snuffelstore", scrape_snuffelstore),
        ("Drinks Corner", scrape_drinkscorner),
        ("Colruyt", scrape_colruyt),
        ("Albert Heijn", scrape_ah),
        ("Delhaize", scrape_delhaize),
        ("Lidl", scrape_lidl),
        ("Jumbo", scrape_jumbo),
    ]
    
    results = {}
    for name, scraper_func in scrapers:
        count = await test_scraper(name, scraper_func)
        results[name] = count
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    for name, count in results.items():
        status = "✅" if count > 0 else "⚠️"
        print(f"{status} {name}: {count} products")
    
    total = sum(results.values())
    print(f"\n📊 Total products found: {total}")
    print("\n✨ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
