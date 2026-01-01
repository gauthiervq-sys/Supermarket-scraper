package utils

import (
	"testing"
)

func TestParseVolumeFromText(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected float64
	}{
		// Single format tests
		{"Single liter", "1.5 L", 1.5},
		{"Single liter no space", "1.5L", 1.5},
		{"Single milliliter", "330 ml", 0.33},
		{"Single milliliter no space", "330ml", 0.33},
		{"Single centiliter", "33 cl", 0.33},
		{"Single centiliter no space", "33cl", 0.33},
		
		// Multi-pack format tests
		{"Multi-pack milliliter", "6 x 330 ml", 1.98},
		{"Multi-pack liter", "4 x 1.5 L", 6.0},
		{"Multi-pack centiliter", "12 x 33 cl", 3.96},
		{"Multi-pack no spaces", "6x330ml", 1.98},
		
		// Edge cases
		{"Empty string", "", 0.0},
		{"No volume", "Coca Cola", 0.0},
		{"Decimal milliliter", "250.5 ml", 0.2505},
		
		// Test that multi-pack takes precedence over single
		// The single regex would match "330 ml" but should not since multi-pack matches first
		{"Multi-pack with extra text", "Pack of 6 x 330 ml bottles", 1.98},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := ParseVolumeFromText(tt.input)
			// Use approximate comparison due to floating point precision
			if !floatEquals(result, tt.expected, 0.01) {
				t.Errorf("ParseVolumeFromText(%q) = %v, want %v", tt.input, result, tt.expected)
			}
		})
	}
}

func TestParseUnitSize(t *testing.T) {
	tests := []struct {
		name         string
		input        string
		expectedSize float64
		expectedUnit string
	}{
		// Single format tests
		{"Single liter", "1.5 L", 1.5, "L"},
		{"Single milliliter", "330 ml", 330, "ML"},
		{"Single centiliter", "33 cl", 33, "CL"},
		
		// Multi-pack format tests - should return unit size, not total
		{"Multi-pack milliliter", "6 x 330 ml", 330, "ML"},
		{"Multi-pack liter", "4 x 1.5 L", 1.5, "L"},
		
		// Edge cases
		{"Empty string", "", 0.0, ""},
		{"No volume", "Coca Cola", 0.0, ""},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			size, unit := ParseUnitSize(tt.input)
			if !floatEquals(size, tt.expectedSize, 0.01) {
				t.Errorf("ParseUnitSize(%q) size = %v, want %v", tt.input, size, tt.expectedSize)
			}
			if unit != tt.expectedUnit {
				t.Errorf("ParseUnitSize(%q) unit = %v, want %v", tt.input, unit, tt.expectedUnit)
			}
		})
	}
}

func TestParseUnitCount(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected int
	}{
		{"Multi-pack 6", "6 x 330 ml", 6},
		{"Multi-pack 12", "12 x 33 cl", 12},
		{"Multi-pack 4", "4 x 1.5 L", 4},
		{"Single item", "1.5 L", 1},
		{"No volume", "Coca Cola", 1},
		{"Empty string", "", 1},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := ParseUnitCount(tt.input)
			if result != tt.expected {
				t.Errorf("ParseUnitCount(%q) = %v, want %v", tt.input, result, tt.expected)
			}
		})
	}
}

func TestCalculatePricePerLiter(t *testing.T) {
	tests := []struct {
		name      string
		price     float64
		volumeStr string
		nameStr   string
		expected  float64
	}{
		{"1.5L bottle", 1.99, "1.5 L", "Coca Cola", 1.32},
		{"330ml can", 0.99, "330 ml", "Coca Cola", 3.00},
		{"6-pack 330ml", 5.94, "6 x 330 ml", "Coca Cola", 3.00},
		{"Volume in name", 1.99, "", "Coca Cola 1.5L", 1.32},
		{"No volume", 1.99, "", "Coca Cola", 0.00},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := CalculatePricePerLiter(tt.price, tt.volumeStr, tt.nameStr)
			if !floatEquals(result, tt.expected, 0.01) {
				t.Errorf("CalculatePricePerLiter(%v, %q, %q) = %v, want %v", 
					tt.price, tt.volumeStr, tt.nameStr, result, tt.expected)
			}
		})
	}
}

func TestConvertToLiters(t *testing.T) {
	tests := []struct {
		name     string
		amount   float64
		unit     string
		expected float64
	}{
		{"Liters", 1.5, "L", 1.5},
		{"Liters lowercase", 2.0, "l", 2.0},
		{"Milliliters", 1000, "ml", 1.0},
		{"Milliliters uppercase", 500, "ML", 0.5},
		{"Centiliters", 100, "cl", 1.0},
		{"Centiliters uppercase", 50, "CL", 0.5},
		{"Unknown unit", 1.5, "kg", 1.5},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := ConvertToLiters(tt.amount, tt.unit)
			if !floatEquals(result, tt.expected, 0.01) {
				t.Errorf("ConvertToLiters(%v, %q) = %v, want %v", tt.amount, tt.unit, result, tt.expected)
			}
		})
	}
}

// Helper function to compare floats with tolerance
func floatEquals(a, b, tolerance float64) bool {
	diff := a - b
	if diff < 0 {
		diff = -diff
	}
	return diff < tolerance
}
