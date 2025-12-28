package database

import (
	"database/sql"
	"log"
	"os"
	"time"

	_ "github.com/mattn/go-sqlite3"
)

var db *sql.DB

// DBProduct represents a product in the database
type DBProduct struct {
	ID            int       `json:"id"`
	Store         string    `json:"store"`
	Name          string    `json:"name"`
	Price         float64   `json:"price"`
	Volume        string    `json:"volume"`
	Image         string    `json:"image"`
	Link          string    `json:"link"`
	PricePerLiter float64   `json:"price_per_liter"`
	LiterValue    float64   `json:"liter_value"`
	UnitCount     int       `json:"unit_count"`
	UnitSize      float64   `json:"unit_size"`
	UnitType      string    `json:"unit_type"`
	PricePerUnit  float64   `json:"price_per_unit"`
	SearchTerm    string    `json:"search_term"`
	ScrapedAt     time.Time `json:"scraped_at"`
	UpdatedAt     time.Time `json:"updated_at"`
}

// Product represents a simpler product structure for saving
type Product struct {
	Store         string
	Name          string
	Price         float64
	Volume        string
	Image         string
	Link          string
	Logo          string
	PricePerLiter float64
	LiterValue    float64
	UnitCount     int
	UnitSize      float64
	UnitType      string
	PricePerUnit  float64
}

// InitDB initializes the database connection and creates tables
func InitDB() {
	dbPath := os.Getenv("DB_PATH")
	if dbPath == "" {
		dbPath = "products.db"
	}

	var err error
	db, err = sql.Open("sqlite3", dbPath)
	if err != nil {
		log.Fatalf("Failed to open database: %v", err)
	}

	// Create products table
	createTableSQL := `
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
	);`

	if _, err := db.Exec(createTableSQL); err != nil {
		log.Fatalf("Failed to create products table: %v", err)
	}

	// Create indexes
	indexes := []string{
		"CREATE INDEX IF NOT EXISTS idx_store ON products(store)",
		"CREATE INDEX IF NOT EXISTS idx_search_term ON products(search_term)",
		"CREATE INDEX IF NOT EXISTS idx_scraped_at ON products(scraped_at)",
		"CREATE INDEX IF NOT EXISTS idx_store_name ON products(store, name)",
	}

	for _, indexSQL := range indexes {
		if _, err := db.Exec(indexSQL); err != nil {
			log.Printf("Warning: Failed to create index: %v", err)
		}
	}

	log.Printf("Database initialized at %s", dbPath)
}

// CloseDB closes the database connection
func CloseDB() {
	if db != nil {
		db.Close()
	}
}

// SaveProductsBatch saves multiple products to the database
func SaveProductsBatch(products []Product, searchTerm string) int {
	if db == nil {
		log.Println("Database not initialized")
		return 0
	}

	savedCount := 0
	now := time.Now()

	insertSQL := `
	INSERT INTO products (
		store, name, price, volume, image, link,
		price_per_liter, liter_value, unit_count, unit_size, unit_type, price_per_unit,
		search_term, scraped_at, updated_at
	) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`

	for _, product := range products {
		_, err := db.Exec(insertSQL,
			product.Store,
			product.Name,
			product.Price,
			product.Volume,
			product.Image,
			product.Link,
			product.PricePerLiter,
			product.LiterValue,
			product.UnitCount,
			product.UnitSize,
			product.UnitType,
			product.PricePerUnit,
			searchTerm,
			now,
			now,
		)
		if err != nil {
			log.Printf("Error saving product %s: %v", product.Name, err)
		} else {
			savedCount++
		}
	}

	return savedCount
}

// GetProductsBySearchTerm retrieves products by search term
func GetProductsBySearchTerm(searchTerm string, limit, offset int) []DBProduct {
	if db == nil {
		return []DBProduct{}
	}

	query := `
	SELECT id, store, name, price, volume, image, link,
		price_per_liter, liter_value, unit_count, unit_size, unit_type, price_per_unit,
		search_term, scraped_at, updated_at
	FROM products
	WHERE search_term = ?
	ORDER BY scraped_at DESC
	LIMIT ? OFFSET ?`

	rows, err := db.Query(query, searchTerm, limit, offset)
	if err != nil {
		log.Printf("Error querying products by search term: %v", err)
		return []DBProduct{}
	}
	defer rows.Close()

	return scanProducts(rows)
}

// GetProductsByStore retrieves products by store name
func GetProductsByStore(store string, limit, offset int) []DBProduct {
	if db == nil {
		return []DBProduct{}
	}

	query := `
	SELECT id, store, name, price, volume, image, link,
		price_per_liter, liter_value, unit_count, unit_size, unit_type, price_per_unit,
		search_term, scraped_at, updated_at
	FROM products
	WHERE store = ?
	ORDER BY scraped_at DESC
	LIMIT ? OFFSET ?`

	rows, err := db.Query(query, store, limit, offset)
	if err != nil {
		log.Printf("Error querying products by store: %v", err)
		return []DBProduct{}
	}
	defer rows.Close()

	return scanProducts(rows)
}

// GetAllProducts retrieves all products with pagination
func GetAllProducts(limit, offset int) []DBProduct {
	if db == nil {
		return []DBProduct{}
	}

	query := `
	SELECT id, store, name, price, volume, image, link,
		price_per_liter, liter_value, unit_count, unit_size, unit_type, price_per_unit,
		search_term, scraped_at, updated_at
	FROM products
	ORDER BY scraped_at DESC
	LIMIT ? OFFSET ?`

	rows, err := db.Query(query, limit, offset)
	if err != nil {
		log.Printf("Error querying all products: %v", err)
		return []DBProduct{}
	}
	defer rows.Close()

	return scanProducts(rows)
}

// DeleteOldProducts deletes products older than specified days
func DeleteOldProducts(days int) int {
	if db == nil {
		return 0
	}

	query := `DELETE FROM products WHERE scraped_at < datetime('now', '-' || ? || ' days')`

	result, err := db.Exec(query, days)
	if err != nil {
		log.Printf("Error deleting old products: %v", err)
		return 0
	}

	deletedCount, _ := result.RowsAffected()
	return int(deletedCount)
}

// GetDatabaseStats returns database statistics
func GetDatabaseStats() map[string]interface{} {
	if db == nil {
		return map[string]interface{}{"error": "Database not initialized"}
	}

	stats := make(map[string]interface{})

	// Total products
	var totalProducts int
	db.QueryRow("SELECT COUNT(*) FROM products").Scan(&totalProducts)
	stats["total_products"] = totalProducts

	// Products per store
	rows, err := db.Query(`
		SELECT store, COUNT(*) as count
		FROM products
		GROUP BY store
		ORDER BY count DESC
	`)
	if err == nil {
		defer rows.Close()
		productsPerStore := make(map[string]int)
		for rows.Next() {
			var store string
			var count int
			rows.Scan(&store, &count)
			productsPerStore[store] = count
		}
		stats["products_per_store"] = productsPerStore
	}

	// Unique search terms
	var uniqueSearchTerms int
	db.QueryRow("SELECT COUNT(DISTINCT search_term) FROM products").Scan(&uniqueSearchTerms)
	stats["unique_search_terms"] = uniqueSearchTerms

	// Most recent scrape
	var mostRecent string
	db.QueryRow("SELECT MAX(scraped_at) FROM products").Scan(&mostRecent)
	stats["most_recent_scrape"] = mostRecent

	dbPath := os.Getenv("DB_PATH")
	if dbPath == "" {
		dbPath = "products.db"
	}
	stats["database_path"] = dbPath

	return stats
}

// scanProducts is a helper function to scan rows into DBProduct slice
func scanProducts(rows *sql.Rows) []DBProduct {
	var products []DBProduct

	for rows.Next() {
		var p DBProduct
		err := rows.Scan(
			&p.ID, &p.Store, &p.Name, &p.Price, &p.Volume, &p.Image, &p.Link,
			&p.PricePerLiter, &p.LiterValue, &p.UnitCount, &p.UnitSize, &p.UnitType, &p.PricePerUnit,
			&p.SearchTerm, &p.ScrapedAt, &p.UpdatedAt,
		)
		if err != nil {
			log.Printf("Error scanning product row: %v", err)
			continue
		}
		products = append(products, p)
	}

	return products
}
