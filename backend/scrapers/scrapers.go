package scrapers

import (
	"fmt"
	"log"
	"net/url"
	"os"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/go-rod/rod"
	"github.com/go-rod/rod/lib/launcher"
)

var debugMode = os.Getenv("DEBUG_MODE") == "true"

// ScraperProduct represents a product scraped from a store
type ScraperProduct struct {
	Store  string
	Name   string
	Price  float64
	Volume string
	Image  string
	Link   string
}

// ScraperResult represents the result of a scraper operation
type ScraperResult struct {
	ScraperName string
	Products    []ScraperProduct
	ElapsedTime float64
	Success     bool
	Error       string
}

// ScraperFunc is a function type for scrapers
type ScraperFunc func(searchTerm string) ([]ScraperProduct, error)

// NewBrowser creates a new rod browser instance
func NewBrowser() *rod.Browser {
	// Try to find system browser first
	browserPath, _ := launcher.LookPath()
	
	// If not found, try common paths (Linux/Unix only - this application runs in Docker with Debian)
	if browserPath == "" {
		commonPaths := []string{
			"/usr/bin/chromium",
			"/usr/bin/chromium-browser",
			"/usr/bin/google-chrome",
		}
		for _, path := range commonPaths {
			if _, err := os.Stat(path); err == nil {
				browserPath = path
				break
			}
		}
	}
	
	// Launch browser in headless mode
	l := launcher.New().
		Headless(true).
		Devtools(false).
		Set("no-sandbox", "").
		Set("disable-setuid-sandbox", "")
	
	// Set browser binary path if found
	if browserPath != "" {
		l = l.Bin(browserPath)
	}
	
	path := l.MustLaunch()

	browser := rod.New().
		ControlURL(path).
		MustConnect()

	return browser
}

// WaitForPageLoad waits for a page to load
func WaitForPageLoad(page *rod.Page, selector string, timeout time.Duration) error {
	_, err := page.Timeout(timeout).Element(selector)
	return err
}

// WaitForPageReady waits for the page to be ready and network to be mostly idle
func WaitForPageReady(page *rod.Page, minWaitSeconds int) {
	// Wait for basic page load
	page.MustWaitLoad()
	
	// Give the page time to render dynamic content
	time.Sleep(time.Duration(minWaitSeconds) * time.Second)
	
	// Wait a bit for any AJAX requests
	time.Sleep(1 * time.Second)
}

// ExtractPrice extracts price from text string
func ExtractPrice(priceText string) float64 {
	if priceText == "" {
		return 0.0
	}

	// Clean up the text
	priceClean := strings.ReplaceAll(priceText, "\n", "")
	priceClean = strings.ReplaceAll(priceClean, "€", "")
	priceClean = strings.ReplaceAll(priceClean, ",", ".")
	priceClean = strings.TrimSpace(priceClean)

	// Extract numeric value using regex
	re := regexp.MustCompile(`(\d+[.,]\d+|\d+)`)
	if match := re.FindString(priceClean); match != "" {
		match = strings.ReplaceAll(match, ",", ".")
		price, err := strconv.ParseFloat(match, 64)
		if err == nil {
			return price
		}
	}

	return 0.0
}

// CompleteURL converts relative URL to absolute
func CompleteURL(urlStr, baseURL string) string {
	if urlStr == "" {
		return ""
	}

	if strings.HasPrefix(urlStr, "http") {
		return urlStr
	} else if strings.HasPrefix(urlStr, "//") {
		return "https:" + urlStr
	} else if strings.HasPrefix(urlStr, "/") {
		return strings.TrimSuffix(baseURL, "/") + urlStr
	} else {
		return strings.TrimSuffix(baseURL, "/") + "/" + urlStr
	}
}

// FilterProductsBySearchTerm filters products by search term
func FilterProductsBySearchTerm(products []ScraperProduct, searchTerm string) []ScraperProduct {
	searchLower := strings.ToLower(searchTerm)
	var filtered []ScraperProduct

	for _, p := range products {
		if strings.Contains(strings.ToLower(p.Name), searchLower) {
			filtered = append(filtered, p)
		}
	}

	return filtered
}

// LogDebug logs debug messages if debug mode is enabled
func LogDebug(storeName string, format string, args ...interface{}) {
	if debugMode {
		message := fmt.Sprintf(format, args...)
		log.Printf("  %s: %s", storeName, message)
	}
}

// ScrapeColruyt scrapes Colruyt products
func ScrapeColruyt(searchTerm string) ([]ScraperProduct, error) {
	safeTerm := url.QueryEscape(searchTerm)
	targetURL := fmt.Sprintf("https://www.collectandgo.be/nl/zoek?searchTerm=%s", safeTerm)
	
	log.Printf("🛒 Colruyt: Checking %s", targetURL)
	
	browser := NewBrowser()
	defer browser.MustClose()
	
	page := browser.MustPage(targetURL)
	defer page.MustClose()
	
	// Wait for page to load properly
	WaitForPageReady(page, 3)
	
	LogDebug("Colruyt", "Page loaded successfully")
	
	var products []ScraperProduct
	
	// Try different selectors for product cards
	selectors := []string{".product-card", ".product-item", "article", "[data-testid='product']"}
	
	for _, selector := range selectors {
		elements, err := page.Elements(selector)
		if err == nil && len(elements) > 0 {
			LogDebug("Colruyt", "Found %d product cards with selector %s", len(elements), selector)
			
			for _, el := range elements {
				product := extractProductFromElement(el, "Colruyt", "https://www.collectandgo.be")
				if product.Name != "" {
					products = append(products, product)
				}
			}
			break
		}
	}
	
	LogDebug("Colruyt", "Found %d total results before filtering", len(products))
	filtered := FilterProductsBySearchTerm(products, searchTerm)
	LogDebug("Colruyt", "Filtered to %d results matching '%s'", len(filtered), searchTerm)
	
	return filtered, nil
}

// extractProductFromElement extracts product information from a DOM element
func extractProductFromElement(element *rod.Element, store, baseURL string) ScraperProduct {
	product := ScraperProduct{Store: store}
	
	// Extract name
	nameSelectors := []string{".product-name", ".product-title", "h3", "h2", "a[class*='title']", "a[class*='name']"}
	for _, sel := range nameSelectors {
		if el, err := element.Element(sel); err == nil {
			if text, err := el.Text(); err == nil {
				product.Name = strings.TrimSpace(text)
				break
			}
		}
	}
	
	// Extract price
	priceSelectors := []string{".price", "[class*='price']", "[data-testid='price']"}
	for _, sel := range priceSelectors {
		if el, err := element.Element(sel); err == nil {
			if text, err := el.Text(); err == nil {
				product.Price = ExtractPrice(text)
				break
			}
		}
	}
	
	// Extract link
	if el, err := element.Element("a"); err == nil {
		if href, err := el.Property("href"); err == nil {
			product.Link = CompleteURL(href.String(), baseURL)
		}
	}
	
	// Extract image
	if el, err := element.Element("img"); err == nil {
		// Try data-src first, then src
		if src, err := el.Property("data-src"); err == nil && src.String() != "" {
			product.Image = CompleteURL(src.String(), baseURL)
		} else if src, err := el.Property("src"); err == nil {
			product.Image = CompleteURL(src.String(), baseURL)
		}
	}
	
	return product
}

// ScrapeAH scrapes Albert Heijn products
func ScrapeAH(searchTerm string) ([]ScraperProduct, error) {
	safeTerm := url.QueryEscape(searchTerm)
	targetURL := fmt.Sprintf("https://www.ah.be/zoeken?query=%s", safeTerm)
	
	log.Printf("🛒 Albert Heijn: Checking %s", targetURL)
	
	browser := NewBrowser()
	defer browser.MustClose()
	
	page := browser.MustPage(targetURL)
	defer page.MustClose()
	
	WaitForPageReady(page, 3)
	
	LogDebug("Albert Heijn", "Page loaded successfully")
	
	var products []ScraperProduct
	
	selectors := []string{".product-card", "[data-testid='product']", "article"}
	
	for _, selector := range selectors {
		elements, err := page.Elements(selector)
		if err == nil && len(elements) > 0 {
			LogDebug("Albert Heijn", "Found %d products", len(elements))
			
			for _, el := range elements {
				product := extractProductFromElement(el, "Albert Heijn", "https://www.ah.be")
				if product.Name != "" {
					products = append(products, product)
				}
			}
			break
		}
	}
	
	filtered := FilterProductsBySearchTerm(products, searchTerm)
	return filtered, nil
}

// ScrapeAldi scrapes Aldi products
func ScrapeAldi(searchTerm string) ([]ScraperProduct, error) {
	safeTerm := url.QueryEscape(searchTerm)
	targetURL := fmt.Sprintf("https://www.aldi.be/nl/zoekresultaten.html?query=%s&searchCategory=Submitted%%20Search", safeTerm)
	
	log.Printf("🛒 Aldi: Checking %s", targetURL)
	
	browser := NewBrowser()
	defer browser.MustClose()
	
	page := browser.MustPage(targetURL)
	defer page.MustClose()
	
	WaitForPageReady(page, 3)
	
	LogDebug("Aldi", "Page loaded successfully")
	
	var products []ScraperProduct
	
	// Get product tiles
	elements, err := page.Elements(".mod-article-tile")
	if err == nil && len(elements) > 0 {
		LogDebug("Aldi", "Found %d product tiles", len(elements))
		
		for _, el := range elements {
			product := extractProductFromElement(el, "Aldi", "https://www.aldi.be")
			if product.Name != "" {
				products = append(products, product)
			}
		}
	}
	
	filtered := FilterProductsBySearchTerm(products, searchTerm)
	return filtered, nil
}

// ScrapeDelhaize scrapes Delhaize products
func ScrapeDelhaize(searchTerm string) ([]ScraperProduct, error) {
	safeTerm := url.QueryEscape(searchTerm)
	targetURL := fmt.Sprintf("https://www.delhaize.be/nl-be/search?text=%s", safeTerm)
	
	log.Printf("🛒 Delhaize: Checking %s", targetURL)
	
	browser := NewBrowser()
	defer browser.MustClose()
	
	page := browser.MustPage(targetURL)
	defer page.MustClose()
	
	WaitForPageReady(page, 3)
	
	var products []ScraperProduct
	
	selectors := []string{".product-tile", ".product-card", "[data-testid='product']"}
	
	for _, selector := range selectors {
		elements, err := page.Elements(selector)
		if err == nil && len(elements) > 0 {
			for _, el := range elements {
				product := extractProductFromElement(el, "Delhaize", "https://www.delhaize.be")
				if product.Name != "" {
					products = append(products, product)
				}
			}
			break
		}
	}
	
	filtered := FilterProductsBySearchTerm(products, searchTerm)
	return filtered, nil
}

// ScrapeLidl scrapes Lidl products
func ScrapeLidl(searchTerm string) ([]ScraperProduct, error) {
	safeTerm := url.QueryEscape(searchTerm)
	targetURL := fmt.Sprintf("https://www.lidl.be/nl/zoeken?q=%s", safeTerm)
	
	log.Printf("🛒 Lidl: Checking %s", targetURL)
	
	browser := NewBrowser()
	defer browser.MustClose()
	
	page := browser.MustPage(targetURL)
	defer page.MustClose()
	
	WaitForPageReady(page, 3)
	
	var products []ScraperProduct
	
	selectors := []string{".product", ".product-grid-box", "[data-testid='product']"}
	
	for _, selector := range selectors {
		elements, err := page.Elements(selector)
		if err == nil && len(elements) > 0 {
			for _, el := range elements {
				product := extractProductFromElement(el, "Lidl", "https://www.lidl.be")
				if product.Name != "" {
					products = append(products, product)
				}
			}
			break
		}
	}
	
	filtered := FilterProductsBySearchTerm(products, searchTerm)
	return filtered, nil
}

// ScrapeJumbo scrapes Jumbo products
func ScrapeJumbo(searchTerm string) ([]ScraperProduct, error) {
	safeTerm := url.QueryEscape(searchTerm)
	targetURL := fmt.Sprintf("https://www.jumbo.be/zoeken?searchTerms=%s", safeTerm)
	
	log.Printf("🛒 Jumbo: Checking %s", targetURL)
	
	browser := NewBrowser()
	defer browser.MustClose()
	
	page := browser.MustPage(targetURL)
	defer page.MustClose()
	
	WaitForPageReady(page, 3)
	
	var products []ScraperProduct
	
	selectors := []string{".product-container", ".jum-product-list-item", "[data-testid='product']"}
	
	for _, selector := range selectors {
		elements, err := page.Elements(selector)
		if err == nil && len(elements) > 0 {
			for _, el := range elements {
				product := extractProductFromElement(el, "Jumbo", "https://www.jumbo.be")
				if product.Name != "" {
					products = append(products, product)
				}
			}
			break
		}
	}
	
	filtered := FilterProductsBySearchTerm(products, searchTerm)
	return filtered, nil
}

// ScrapeCarrefour scrapes Carrefour products
func ScrapeCarrefour(searchTerm string) ([]ScraperProduct, error) {
	safeTerm := url.QueryEscape(searchTerm)
	targetURL := fmt.Sprintf("https://www.carrefour.be/nl/search?q=%s", safeTerm)
	
	log.Printf("🛒 Carrefour: Checking %s", targetURL)
	
	browser := NewBrowser()
	defer browser.MustClose()
	
	page := browser.MustPage(targetURL)
	defer page.MustClose()
	
	WaitForPageReady(page, 3)
	
	var products []ScraperProduct
	
	selectors := []string{".product-tile", ".product-card", "[data-testid='product']"}
	
	for _, selector := range selectors {
		elements, err := page.Elements(selector)
		if err == nil && len(elements) > 0 {
			for _, el := range elements {
				product := extractProductFromElement(el, "Carrefour", "https://www.carrefour.be")
				if product.Name != "" {
					products = append(products, product)
				}
			}
			break
		}
	}
	
	filtered := FilterProductsBySearchTerm(products, searchTerm)
	return filtered, nil
}

// ScrapePrikentik scrapes Prik&Tik products
func ScrapePrikentik(searchTerm string) ([]ScraperProduct, error) {
	safeTerm := url.QueryEscape(searchTerm)
	targetURL := fmt.Sprintf("https://www.prikentik.be/catalogsearch/result/?q=%s", safeTerm)
	
	log.Printf("🛒 Prik&Tik: Checking %s", targetURL)
	
	browser := NewBrowser()
	defer browser.MustClose()
	
	page := browser.MustPage(targetURL)
	defer page.MustClose()
	
	WaitForPageReady(page, 3)
	
	var products []ScraperProduct
	
	selectors := []string{".product-item", ".item", "[data-testid='product']"}
	
	for _, selector := range selectors {
		elements, err := page.Elements(selector)
		if err == nil && len(elements) > 0 {
			for _, el := range elements {
				product := extractProductFromElement(el, "Prik&Tik", "https://www.prikentik.be")
				if product.Name != "" {
					products = append(products, product)
				}
			}
			break
		}
	}
	
	filtered := FilterProductsBySearchTerm(products, searchTerm)
	return filtered, nil
}

// ScrapeSnuffelstore scrapes Snuffelstore products
func ScrapeSnuffelstore(searchTerm string) ([]ScraperProduct, error) {
	safeTerm := url.QueryEscape(searchTerm)
	targetURL := fmt.Sprintf("https://www.snuffelstore.be/?s=%s&post_type=product", safeTerm)
	
	log.Printf("🛒 Snuffelstore: Checking %s", targetURL)
	
	browser := NewBrowser()
	defer browser.MustClose()
	
	page := browser.MustPage(targetURL)
	defer page.MustClose()
	
	WaitForPageReady(page, 3)
	
	var products []ScraperProduct
	
	selectors := []string{".product", ".product-small", ".woocommerce-loop-product"}
	
	for _, selector := range selectors {
		elements, err := page.Elements(selector)
		if err == nil && len(elements) > 0 {
			for _, el := range elements {
				product := extractProductFromElement(el, "Snuffelstore", "https://www.snuffelstore.be")
				if product.Name != "" {
					products = append(products, product)
				}
			}
			break
		}
	}
	
	filtered := FilterProductsBySearchTerm(products, searchTerm)
	return filtered, nil
}

// ScrapeDrinkscorner scrapes Drinks Corner products
func ScrapeDrinkscorner(searchTerm string) ([]ScraperProduct, error) {
	safeTerm := url.QueryEscape(searchTerm)
	targetURL := fmt.Sprintf("https://drinkscorner.be/?s=%s&post_type=product", safeTerm)
	
	log.Printf("🛒 Drinks Corner: Checking %s", targetURL)
	
	browser := NewBrowser()
	defer browser.MustClose()
	
	page := browser.MustPage(targetURL)
	defer page.MustClose()
	
	WaitForPageReady(page, 3)
	
	var products []ScraperProduct
	
	selectors := []string{".product", ".product-small", ".woocommerce-loop-product"}
	
	for _, selector := range selectors {
		elements, err := page.Elements(selector)
		if err == nil && len(elements) > 0 {
			for _, el := range elements {
				product := extractProductFromElement(el, "Drinks Corner", "https://drinkscorner.be")
				if product.Name != "" {
					products = append(products, product)
				}
			}
			break
		}
	}
	
	filtered := FilterProductsBySearchTerm(products, searchTerm)
	return filtered, nil
}
