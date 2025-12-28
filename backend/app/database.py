"""
Database module for storing scraped product information.
Uses SQLite for simplicity - no external database setup required.
"""
import sqlite3
import logging
import os
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Database file path
DB_PATH = os.getenv('DB_PATH', 'products.db')


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()


def init_database():
    """Initialize the database and create tables if they don't exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store TEXT NOT NULL,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                volume TEXT,
                image TEXT,
                link TEXT,
                price_per_liter REAL,
                liter_value REAL,
                unit_count INTEGER,
                unit_size REAL,
                unit_type TEXT,
                price_per_unit REAL,
                search_term TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better query performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_store ON products(store)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_search_term ON products(search_term)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_scraped_at ON products(scraped_at)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_store_name ON products(store, name)
        ''')
        
        conn.commit()
        logger.info(f"Database initialized at {DB_PATH}")


def save_product(product: Dict, search_term: str) -> int:
    """
    Save a single product to the database.
    
    Args:
        product: Product dictionary with keys: store, name, price, volume, image, link, etc.
        search_term: The search term used to find this product
        
    Returns:
        The ID of the inserted product
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO products (
                store, name, price, volume, image, link,
                price_per_liter, liter_value, unit_count, unit_size, unit_type, price_per_unit,
                search_term, scraped_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            product.get('store', ''),
            product.get('name', ''),
            product.get('price', 0.0),
            product.get('volume', ''),
            product.get('image', ''),
            product.get('link', ''),
            product.get('price_per_liter', 0.0),
            product.get('liter_value', 0.0),
            product.get('unit_count', 1),
            product.get('unit_size', 0.0),
            product.get('unit_type', ''),
            product.get('price_per_unit', 0.0),
            search_term,
            datetime.now(),
            datetime.now()
        ))
        
        return cursor.lastrowid


def save_products_batch(products: List[Dict], search_term: str) -> int:
    """
    Save multiple products to the database in a batch.
    
    Args:
        products: List of product dictionaries
        search_term: The search term used to find these products
        
    Returns:
        Number of products saved
    """
    saved_count = 0
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        for product in products:
            try:
                cursor.execute('''
                    INSERT INTO products (
                        store, name, price, volume, image, link,
                        price_per_liter, liter_value, unit_count, unit_size, unit_type, price_per_unit,
                        search_term, scraped_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    product.get('store', ''),
                    product.get('name', ''),
                    product.get('price', 0.0),
                    product.get('volume', ''),
                    product.get('image', ''),
                    product.get('link', ''),
                    product.get('price_per_liter', 0.0),
                    product.get('liter_value', 0.0),
                    product.get('unit_count', 1),
                    product.get('unit_size', 0.0),
                    product.get('unit_type', ''),
                    product.get('price_per_unit', 0.0),
                    search_term,
                    datetime.now(),
                    datetime.now()
                ))
                saved_count += 1
            except Exception as e:
                logger.error(f"Error saving product {product.get('name', 'unknown')}: {e}")
        
        conn.commit()
    
    return saved_count


def get_products_by_search_term(search_term: str, limit: int = 100) -> List[Dict]:
    """
    Retrieve products from the database by search term.
    
    Args:
        search_term: The search term to filter by
        limit: Maximum number of products to return
        
    Returns:
        List of product dictionaries
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM products
            WHERE search_term = ?
            ORDER BY scraped_at DESC
            LIMIT ?
        ''', (search_term, limit))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_all_products(limit: int = 1000, offset: int = 0) -> List[Dict]:
    """
    Retrieve all products from the database with pagination.
    
    Args:
        limit: Maximum number of products to return
        offset: Number of products to skip
        
    Returns:
        List of product dictionaries
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM products
            ORDER BY scraped_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_products_by_store(store: str, limit: int = 100) -> List[Dict]:
    """
    Retrieve products from the database by store name.
    
    Args:
        store: The store name to filter by
        limit: Maximum number of products to return
        
    Returns:
        List of product dictionaries
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM products
            WHERE store = ?
            ORDER BY scraped_at DESC
            LIMIT ?
        ''', (store, limit))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def delete_old_products(days: int = 7) -> int:
    """
    Delete products older than specified number of days.
    
    Args:
        days: Number of days to keep products
        
    Returns:
        Number of products deleted
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM products
            WHERE scraped_at < datetime('now', '-' || ? || ' days')
        ''', (days,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        return deleted_count


def get_database_stats() -> Dict:
    """
    Get statistics about the database.
    
    Returns:
        Dictionary with database statistics
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Total products
        cursor.execute('SELECT COUNT(*) FROM products')
        total_products = cursor.fetchone()[0]
        
        # Products per store
        cursor.execute('''
            SELECT store, COUNT(*) as count
            FROM products
            GROUP BY store
            ORDER BY count DESC
        ''')
        products_per_store = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Unique search terms
        cursor.execute('SELECT COUNT(DISTINCT search_term) FROM products')
        unique_search_terms = cursor.fetchone()[0]
        
        # Most recent scrape
        cursor.execute('SELECT MAX(scraped_at) FROM products')
        most_recent = cursor.fetchone()[0]
        
        return {
            'total_products': total_products,
            'products_per_store': products_per_store,
            'unique_search_terms': unique_search_terms,
            'most_recent_scrape': most_recent,
            'database_path': DB_PATH
        }


# Initialize database on module import
try:
    init_database()
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
