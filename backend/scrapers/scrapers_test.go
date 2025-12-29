package scrapers

import (
	"testing"
	"time"
)

// TestNewBrowser tests that NewBrowser can successfully create a browser instance
func TestNewBrowser(t *testing.T) {
	// Create browser instance
	browser := NewBrowser()
	if browser == nil {
		t.Fatal("NewBrowser returned nil")
	}
	
	// Clean up
	defer browser.MustClose()
	
	// Try to create a simple page to verify browser works
	page := browser.MustPage("data:text/html,<h1>Test</h1>")
	if page == nil {
		t.Fatal("Failed to create page")
	}
	defer page.MustClose()
	
	// Wait briefly to ensure page loads
	time.Sleep(100 * time.Millisecond)
	
	// Verify we can get page content
	html, err := page.HTML()
	if err != nil {
		t.Fatalf("Failed to get page HTML: %v", err)
	}
	
	if html == "" {
		t.Fatal("Page HTML is empty")
	}
}

// TestExtractPrice tests the price extraction function
func TestExtractPrice(t *testing.T) {
	tests := []struct {
		input    string
		expected float64
	}{
		{"€10.99", 10.99},
		{"10,99", 10.99},
		{"€ 10.50", 10.50},
		{"15", 15.0},
		{"", 0.0},
		{"no price", 0.0},
	}
	
	for _, test := range tests {
		result := ExtractPrice(test.input)
		if result != test.expected {
			t.Errorf("ExtractPrice(%q) = %v, expected %v", test.input, result, test.expected)
		}
	}
}

// TestCompleteURL tests the URL completion function
func TestCompleteURL(t *testing.T) {
	tests := []struct {
		url      string
		base     string
		expected string
	}{
		{"https://example.com/page", "https://example.com", "https://example.com/page"},
		{"/page", "https://example.com", "https://example.com/page"},
		{"//cdn.example.com/image.jpg", "https://example.com", "https://cdn.example.com/image.jpg"},
		{"page", "https://example.com", "https://example.com/page"},
		{"", "https://example.com", ""},
	}
	
	for _, test := range tests {
		result := CompleteURL(test.url, test.base)
		if result != test.expected {
			t.Errorf("CompleteURL(%q, %q) = %q, expected %q", test.url, test.base, result, test.expected)
		}
	}
}
