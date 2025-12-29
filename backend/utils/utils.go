package utils

import (
	"regexp"
	"sort"
	"strconv"
	"strings"
)

// ConvertToLiters converts volume to liters based on unit
func ConvertToLiters(amount float64, unit string) float64 {
	switch strings.ToLower(unit) {
	case "ml":
		return amount / 1000
	case "cl":
		return amount / 100
	default:
		return amount
	}
}

// ParseVolumeFromText extracts volume in liters from text
func ParseVolumeFromText(text string) float64 {
	if text == "" {
		return 0.0
	}
	text = strings.ToLower(strings.ReplaceAll(text, ",", "."))

	// Match multi-pack format: "6 x 330 ml"
	multiRe := regexp.MustCompile(`(\d+)\s*x\s*([\d\.]+)\s*(l|cl|ml)`)
	if match := multiRe.FindStringSubmatch(text); match != nil {
		count, _ := strconv.Atoi(match[1])
		size, _ := strconv.ParseFloat(match[2], 64)
		unit := match[3]
		total := float64(count) * size
		return ConvertToLiters(total, unit)
	}

	// Match single format: "1.5 L" or "330ml"
	singleRe := regexp.MustCompile(`(?<!x)\s*([\d\.]+)\s*(l|cl|ml)`)
	if match := singleRe.FindStringSubmatch(text); match != nil {
		size, _ := strconv.ParseFloat(match[1], 64)
		unit := match[2]
		return ConvertToLiters(size, unit)
	}

	return 0.0
}

// ParseUnitCount extracts the number of units from text like "6 x 330 ml"
func ParseUnitCount(text string) int {
	if text == "" {
		return 1
	}
	text = strings.ToLower(text)

	re := regexp.MustCompile(`(\d+)\s*x\s*[\d\.]+\s*(l|cl|ml)`)
	if match := re.FindStringSubmatch(text); match != nil {
		count, _ := strconv.Atoi(match[1])
		return count
	}

	return 1
}

// ParseUnitSize extracts unit size and type from text
func ParseUnitSize(text string) (float64, string) {
	if text == "" {
		return 0.0, ""
	}
	text = strings.ToLower(strings.ReplaceAll(text, ",", "."))

	// Check for multi-pack format like "6 x 330 ml"
	multiRe := regexp.MustCompile(`\d+\s*x\s*([\d\.]+)\s*(l|cl|ml)`)
	if match := multiRe.FindStringSubmatch(text); match != nil {
		size, _ := strconv.ParseFloat(match[1], 64)
		unit := strings.ToUpper(match[2])
		return size, unit
	}

	// Check for single format like "1.5 L" or "330ml"
	singleRe := regexp.MustCompile(`(?<!x)\s*([\d\.]+)\s*(l|cl|ml)`)
	if match := singleRe.FindStringSubmatch(text); match != nil {
		size, _ := strconv.ParseFloat(match[1], 64)
		unit := strings.ToUpper(match[2])
		return size, unit
	}

	return 0.0, ""
}

// CalculatePricePerLiter calculates price per liter
func CalculatePricePerLiter(price float64, volumeStr, name string) float64 {
	liters := ParseVolumeFromText(volumeStr)
	if liters == 0 {
		liters = ParseVolumeFromText(name)
	}
	if liters == 0 {
		return 0.0
	}
	result := price / liters
	return float64(int(result*100)) / 100 // Round to 2 decimal places
}

// ExtractPriceFromText extracts numeric price from text
func ExtractPriceFromText(priceText string) float64 {
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

// CompleteURL converts a relative URL to absolute
func CompleteURL(url, baseURL string) string {
	if url == "" {
		return ""
	}

	if strings.HasPrefix(url, "http") {
		return url
	} else if strings.HasPrefix(url, "//") {
		return "https:" + url
	} else if strings.HasPrefix(url, "/") {
		return strings.TrimSuffix(baseURL, "/") + url
	} else {
		return strings.TrimSuffix(baseURL, "/") + "/" + url
	}
}

// Product represents a product with price information
type Product struct {
	Store         string
	Name          string
	Price         float64
	Volume        string
	Image         string
	Link          string
	PricePerLiter float64
}

// SortProductsByPricePerLiter sorts products by price per liter
func SortProductsByPricePerLiter(products []Product) {
	sort.Slice(products, func(i, j int) bool {
		priceI := products[i].PricePerLiter
		priceJ := products[j].PricePerLiter
		if priceI == 0 {
			priceI = 999
		}
		if priceJ == 0 {
			priceJ = 999
		}
		return priceI < priceJ
	})
}
