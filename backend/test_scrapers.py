#!/usr/bin/env python3
"""
Test script to verify scrapers and database functionality.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.scrapers.aldi import scrape_aldi
from app.scrapers.prikentik import scrape_prikentik
from app import database

async def test_aldi():
    """Test Aldi scraper with individual product page visits."""
    print("\n" + "="*60)
    print("Testing Aldi Scraper")
    print("="*60)
    
    try:
        results = await scrape_aldi("cola")
        print(f"✅ Aldi scraper completed successfully")
        print(f"   Found {len(results)} products")
        if results:
            print(f"   Sample product: {results[0]['name']} - €{results[0]['price']}")
        return results
    except Exception as e:
        print(f"❌ Aldi scraper failed: {e}")
        return []

async def test_prikentik():
    """Test Prik&Tik scraper with individual product page visits."""
    print("\n" + "="*60)
    print("Testing Prik&Tik Scraper")
    print("="*60)
    
    try:
        results = await scrape_prikentik("cola")
        print(f"✅ Prik&Tik scraper completed successfully")
        print(f"   Found {len(results)} products")
        if results:
            print(f"   Sample product: {results[0]['name']} - €{results[0]['price']}")
        return results
    except Exception as e:
        print(f"❌ Prik&Tik scraper failed: {e}")
        return []

def test_database(products):
    """Test database functionality."""
    print("\n" + "="*60)
    print("Testing Database Functionality")
    print("="*60)
    
    try:
        # Save products
        if products:
            saved = database.save_products_batch(products, "cola")
            print(f"✅ Saved {saved} products to database")
        
        # Get stats
        stats = database.get_database_stats()
        print(f"✅ Database stats:")
        print(f"   Total products: {stats['total_products']}")
        print(f"   Unique search terms: {stats['unique_search_terms']}")
        print(f"   Products per store: {stats['products_per_store']}")
        
        # Query products
        retrieved = database.get_products_by_search_term("cola", limit=5)
        print(f"✅ Retrieved {len(retrieved)} products from database")
        
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("\n🚀 Starting Supermarket Scraper Tests")
    print("This will test enhanced scrapers and database functionality")
    
    # Test scrapers
    aldi_results = await test_aldi()
    prikentik_results = await test_prikentik()
    
    # Test database
    all_results = aldi_results + prikentik_results
    db_success = test_database(all_results)
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"✅ Aldi: {len(aldi_results)} products")
    print(f"✅ Prik&Tik: {len(prikentik_results)} products")
    print(f"✅ Database: {'Working' if db_success else 'Failed'}")
    print("\n✨ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
