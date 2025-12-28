package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"sync"
	"time"

	"github.com/gauthiervq-sys/Supermarket-scraper/backend/scrapers"
	"github.com/gauthiervq-sys/Supermarket-scraper/backend/database"
	"github.com/gauthiervq-sys/Supermarket-scraper/backend/utils"
)

var (
	debugMode = os.Getenv("DEBUG_MODE") == "true"
)

// StoreLogos contains CDN URLs for store logos
var StoreLogos = map[string]string{
	"Colruyt":        "https://cdn.cookielaw.org/logos/01b5df24-cb0b-44a1-90e6-afd3f2e7bea0/36dcc7e0-97a6-422b-b3ad-c90e49082efd/91f51b8c-c0a7-4849-8b20-86e0fc38eeb7/Colruyt_Group_logo.png",
	"Albert Heijn":   "https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/Albert_Heijn_logo.svg/274px-Albert_Heijn_logo.svg.png",
	"Aldi":           "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/Aldi_Nord_201x_logo.svg/256px-Aldi_Nord_201x_logo.svg.png",
	"Delhaize":       "https://static.delhaize.be/logo_delhaize.svg",
	"Lidl":           "https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Lidl-Logo.svg/1024px-Lidl-Logo.svg.png",
	"Jumbo":          "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ee/Jumbo_Logo.svg/1200px-Jumbo_Logo.svg.png",
	"Carrefour":      "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Carrefour_logo.svg/1024px-Carrefour_logo.svg.png",
	"Prik&Tik":       "https://www.prikentik.be/static/version1733984638/frontend/PrikEnTik/default/nl_BE/images/logo.svg",
	"Snuffelstore":   "https://www.snuffelstore.be/wp-content/uploads/2021/04/snuffelstore-logo-1.png",
	"Drinks Corner":  "https://drinkscorner.be/wp-content/uploads/2023/10/DrinksCorner-Logo-web-150x64.png",
}

// Product represents a product from a supermarket
type Product struct {
	Store         string  `json:"store"`
	Name          string  `json:"name"`
	Price         float64 `json:"price"`
	Volume        string  `json:"volume"`
	Image         string  `json:"image"`
	Link          string  `json:"link"`
	Logo          string  `json:"logo"`
	PricePerLiter float64 `json:"price_per_liter"`
	LiterValue    float64 `json:"liter_value"`
	UnitCount     int     `json:"unit_count"`
	UnitSize      float64 `json:"unit_size"`
	UnitType      string  `json:"unit_type"`
	PricePerUnit  float64 `json:"price_per_unit"`
}

// ScraperStatus represents the status of a scraper
type ScraperStatus struct {
	Name        string  `json:"name"`
	Success     bool    `json:"success"`
	Error       string  `json:"error,omitempty"`
	Count       int     `json:"count"`
	ElapsedTime float64 `json:"elapsed_time"`
}

// SearchResponse represents the response for the search endpoint
type SearchResponse struct {
	Products         []Product       `json:"products"`
	ScraperStatuses  []ScraperStatus `json:"scraperStatuses"`
	TotalElapsedTime float64         `json:"totalElapsedTime"`
	DebugMode        bool            `json:"debugMode"`
}

func enableCORS(w http.ResponseWriter) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "*")
}

func searchHandler(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == "OPTIONS" {
		w.WriteHeader(http.StatusOK)
		return
	}

	query := r.URL.Query().Get("q")
	if len(query) < 2 {
		http.Error(w, "Query parameter 'q' must be at least 2 characters", http.StatusBadRequest)
		return
	}

	log.Println("============================================================")
	log.Printf("🚦 NEW SEARCH REQUEST: '%s'", query)
	log.Println("============================================================")

	startTime := time.Now()

	// Run all scrapers concurrently
	var wg sync.WaitGroup
	scraperFuncs := []struct {
		name   string
		scrape scrapers.ScraperFunc
	}{
		{"Colruyt", scrapers.ScrapeColruyt},
		{"Albert Heijn", scrapers.ScrapeAH},
		{"Aldi", scrapers.ScrapeAldi},
		{"Delhaize", scrapers.ScrapeDelhaize},
		{"Lidl", scrapers.ScrapeLidl},
		{"Jumbo", scrapers.ScrapeJumbo},
		{"Carrefour", scrapers.ScrapeCarrefour},
		{"Prik&Tik", scrapers.ScrapePrikentik},
		{"Snuffelstore", scrapers.ScrapeSnuffelstore},
		{"Drinks Corner", scrapers.ScrapeDrinkscorner},
	}

	resultsChan := make(chan scrapers.ScraperResult, len(scraperFuncs))

	// Limit concurrent scrapers to 5
	semaphore := make(chan struct{}, 5)

	for _, scraper := range scraperFuncs {
		wg.Add(1)
		go func(name string, sf scrapers.ScraperFunc) {
			defer wg.Done()
			semaphore <- struct{}{} // Acquire
			defer func() { <-semaphore }() // Release

			scraperStartTime := time.Now()
			log.Printf("🔍 Starting scraper: %s", name)

			results, err := sf(query)
			elapsed := time.Since(scraperStartTime).Seconds()

			result := scrapers.ScraperResult{
				ScraperName: name,
				Products:    results,
				ElapsedTime: elapsed,
				Success:     err == nil,
			}
			if err != nil {
				result.Error = err.Error()
				log.Printf("❌ Error in %s after %.2fs: %v", name, elapsed, err)
			} else {
				if debugMode {
					log.Printf("✅ %s completed in %.2fs - Found %d products", name, elapsed, len(results))
				} else {
					log.Printf("✅ %s - %d products in %.2fs", name, len(results), elapsed)
				}
			}
			resultsChan <- result
		}(scraper.name, scraper.scrape)
	}

	wg.Wait()
	close(resultsChan)

	// Collect all results
	var allProducts []Product
	var allDBProducts []database.Product
	var scraperStatuses []ScraperStatus

	for result := range resultsChan {
		status := ScraperStatus{
			Name:        result.ScraperName,
			Success:     result.Success,
			Error:       result.Error,
			Count:       len(result.Products),
			ElapsedTime: result.ElapsedTime,
		}
		scraperStatuses = append(scraperStatuses, status)

		for _, p := range result.Products {
			product := Product{
				Store:  p.Store,
				Name:   p.Name,
				Price:  p.Price,
				Volume: p.Volume,
				Image:  p.Image,
				Link:   p.Link,
			}

			// Calculate price per liter
			product.PricePerLiter = utils.CalculatePricePerLiter(p.Price, p.Volume, p.Name)
			product.LiterValue = utils.ParseVolumeFromText(p.Volume)
			if product.LiterValue == 0 {
				product.LiterValue = utils.ParseVolumeFromText(p.Name)
			}
			if product.Volume == "" {
				if product.LiterValue < 1 {
					product.Volume = fmt.Sprintf("%dcl", int(product.LiterValue*100))
				} else {
					product.Volume = fmt.Sprintf("%.1fL", product.LiterValue)
				}
			}

			// Calculate unit information for multi-packs
			unitCount := utils.ParseUnitCount(p.Volume)
			if unitCount == 1 {
				unitCount = utils.ParseUnitCount(p.Name)
			}

			unitSize, unitType := utils.ParseUnitSize(p.Volume)
			if unitSize == 0.0 {
				unitSize, unitType = utils.ParseUnitSize(p.Name)
			}

			product.UnitCount = unitCount
			product.UnitSize = unitSize
			product.UnitType = unitType

			// Calculate price per unit (can/bottle)
			if unitCount > 1 {
				product.PricePerUnit = p.Price / float64(unitCount)
			} else {
				product.PricePerUnit = p.Price
			}

			// Assign logo
			product.Logo = StoreLogos[p.Store]

			if product.Price > 0 {
				allProducts = append(allProducts, product)
				
				// Create database product
				dbProduct := database.Product{
					Store:         product.Store,
					Name:          product.Name,
					Price:         product.Price,
					Volume:        product.Volume,
					Image:         product.Image,
					Link:          product.Link,
					Logo:          product.Logo,
					PricePerLiter: product.PricePerLiter,
					LiterValue:    product.LiterValue,
					UnitCount:     product.UnitCount,
					UnitSize:      product.UnitSize,
					UnitType:      product.UnitType,
					PricePerUnit:  product.PricePerUnit,
				}
				allDBProducts = append(allDBProducts, dbProduct)
			}
		}
	}

	// Sort by price per liter
	sortProductsByPricePerLiter(allProducts)

	// Save to database
	savedCount := database.SaveProductsBatch(allDBProducts, query)
	log.Printf("💾 Saved %d products to database", savedCount)

	totalElapsed := time.Since(startTime).Seconds()

	log.Println("============================================================")
	log.Printf("✅ SEARCH COMPLETED in %.2fs", totalElapsed)
	log.Printf("📊 Total products found: %d", len(allProducts))

	successCount := 0
	for _, s := range scraperStatuses {
		if s.Success {
			successCount++
		}
	}
	log.Printf("🏪 Successful scrapers: %d/%d", successCount, len(scraperStatuses))

	if debugMode {
		for _, status := range scraperStatuses {
			statusChar := "✓"
			if !status.Success {
				statusChar = "✗"
			}
			log.Printf("  • %s: %s (%d products, %.2fs)", status.Name, statusChar, status.Count, status.ElapsedTime)
		}
	}
	log.Println("============================================================")

	response := SearchResponse{
		Products:         allProducts,
		ScraperStatuses:  scraperStatuses,
		TotalElapsedTime: totalElapsed,
		DebugMode:        debugMode,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func getProductsHandler(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == "OPTIONS" {
		w.WriteHeader(http.StatusOK)
		return
	}

	searchTerm := r.URL.Query().Get("search_term")
	store := r.URL.Query().Get("store")
	limit := 100
	offset := 0

	if l := r.URL.Query().Get("limit"); l != "" {
		fmt.Sscanf(l, "%d", &limit)
		if limit < 1 {
			limit = 1
		}
		if limit > 1000 {
			limit = 1000
		}
	}

	if o := r.URL.Query().Get("offset"); o != "" {
		fmt.Sscanf(o, "%d", &offset)
		if offset < 0 {
			offset = 0
		}
	}

	var products []database.DBProduct
	if searchTerm != "" {
		products = database.GetProductsBySearchTerm(searchTerm, limit, offset)
	} else if store != "" {
		products = database.GetProductsByStore(store, limit, offset)
	} else {
		products = database.GetAllProducts(limit, offset)
	}

	response := map[string]interface{}{
		"products": products,
		"count":    len(products),
		"limit":    limit,
		"offset":   offset,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func getDatabaseStatsHandler(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == "OPTIONS" {
		w.WriteHeader(http.StatusOK)
		return
	}

	stats := database.GetDatabaseStats()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(stats)
}

func cleanupDatabaseHandler(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == "OPTIONS" {
		w.WriteHeader(http.StatusOK)
		return
	}

	days := 7
	if d := r.URL.Query().Get("days"); d != "" {
		fmt.Sscanf(d, "%d", &days)
		if days < 1 {
			days = 1
		}
		if days > 365 {
			days = 365
		}
	}

	deletedCount := database.DeleteOldProducts(days)

	response := map[string]interface{}{
		"message":        fmt.Sprintf("Deleted %d products older than %d days", deletedCount, days),
		"deleted_count":  deletedCount,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func sortProductsByPricePerLiter(products []Product) {
	for i := 0; i < len(products); i++ {
		for j := i + 1; j < len(products); j++ {
			priceI := products[i].PricePerLiter
			priceJ := products[j].PricePerLiter
			if priceI == 0 {
				priceI = 999
			}
			if priceJ == 0 {
				priceJ = 999
			}
			if priceI > priceJ {
				products[i], products[j] = products[j], products[i]
			}
		}
	}
}

func main() {
	// Initialize database
	database.InitDB()
	defer database.CloseDB()

	// Set up logging
	if debugMode {
		log.Println("DEBUG_MODE enabled")
	}

	http.HandleFunc("/search", searchHandler)
	http.HandleFunc("/products", getProductsHandler)
	http.HandleFunc("/database/stats", getDatabaseStatsHandler)
	http.HandleFunc("/database/cleanup", cleanupDatabaseHandler)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8100"
	}

	log.Printf("🚀 Server starting on port %s", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
