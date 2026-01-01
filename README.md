# Supermarket Scraper - BE Supermarkt Scanner Ultimate

A web application that scrapes and compares prices from multiple Belgian supermarkets in real-time. Find the best deals on products across Colruyt, Albert Heijn, Aldi, Delhaize, Lidl, Jumbo, Carrefour, Prik&Tik, Snuffelstore, and Drinks Corner.

## ⚡ Recent Improvements

**Migrated to Go with go-rod/rod for Better Performance and Reliability!**

The scraping engine has been completely rewritten in Go using the go-rod/rod library:
- ✅ **Concurrent scraping** with proper goroutine management
- ✅ **Native browser automation** with Rod (Chrome DevTools Protocol)
- ✅ **Better performance** with Go's speed and efficiency
- ✅ **Improved reliability** with proper error handling and timeouts
- ✅ **Type safety** with Go's strong typing system
- ✅ **Easy deployment** with single binary compilation
- ✅ **Lower memory footprint** compared to Python-based solutions

## Features

- 🔍 Real-time product search across 10 Belgian supermarkets
- 💰 Price comparison with price-per-liter/kg calculations
- 🏪 Store logos and product images
- 📊 Filter results by product size/volume
- ⚡ Parallel scraping for faster results (up to 5 concurrent scrapers)
- 🎨 Modern, responsive UI with dark mode
- 🐛 **Debug mode** to see what sites are being checked and troubleshoot scraping issues
- 💾 **Database storage** - All scraped products are automatically saved to a SQLite database
- 🔗 **Enhanced scraping** - Uses go-rod/rod for reliable browser automation

## Prerequisites

Before you begin, ensure you have the following installed:

- **Go 1.24+** - [Download Go](https://golang.org/dl/)
- **Node.js 16+** and **npm** - [Download Node.js](https://nodejs.org/)
- **Git** - [Download Git](https://git-scm.com/downloads/)
- **Chromium or Chrome browser** - Required for Rod browser automation

Optional (for containerized deployment):
- **Docker** and **Docker Compose** - [Download Docker](https://www.docker.com/get-started)

## Installation from Scratch

### Quick Setup (Recommended)

Use the automated setup script to install everything:

```bash
# Clone and setup in one go
git clone https://github.com/gauthiervq-sys/Supermarket-scraper.git
cd Supermarket-scraper
./setup.sh
```

The setup script will:
- ✅ Check for required prerequisites (Go, Node.js, npm)
- ✅ Download all Go dependencies
- ✅ Build the backend application
- ✅ Install all Node.js dependencies
- ✅ Provide instructions for running the application

### Manual Setup

If you prefer to set up manually:

#### 1. Clone the Repository

```bash
git clone https://github.com/gauthiervq-sys/Supermarket-scraper.git
cd Supermarket-scraper
```

#### 2. Backend Setup (Go)

Navigate to the backend directory and set up the Go environment:

```bash
cd backend

# Download Go dependencies
go mod download

# Build the application
go build -o supermarket-scraper main.go
```

#### 3. Frontend Setup

Navigate to the frontend directory and install dependencies:

```bash
cd ../frontend

# Install Node.js dependencies
npm install
```

## Running the Application

### Option 1: Local Development

You need to run both the backend and frontend servers simultaneously.

#### Start the Backend Server

```bash
# From the backend directory
cd backend

# Run the Go application
./supermarket-scraper
# Or on Windows:
# supermarket-scraper.exe

# The server will start on port 8100 by default
```

The backend API will be available at `http://localhost:8100`

**Optional environment variables:**
```bash
# Enable debug mode for detailed logging
export DEBUG_MODE=true

# Set custom port (default is 8100)
export PORT=8200

# Set custom database path (default is products.db)
export DB_PATH=/path/to/database.db

# Then run the server
./supermarket-scraper
```

#### Start the Frontend Server

Open a new terminal window:

```bash
# From the frontend directory
cd frontend

# Run the development server
npm run dev
```

The frontend will be available at `http://localhost:3100` (or another port if 3100 is busy)

### Option 2: Docker Compose (Easiest)

If you have Docker installed, you can run everything with one command:

```bash
# From the project root directory
docker-compose up --build
```

This will:
- Build and start the backend on port 8100
- Build and start the frontend on port 3100
- Handle all dependencies automatically

Access the application at `http://localhost:3100`

To stop the containers:
```bash
docker-compose down
```

## Updating the Application

### Update from Git

To get the latest changes from the repository:

```bash
# Pull the latest changes
git pull origin main

# Update backend dependencies
cd backend
go mod download
go build -o supermarket-scraper main.go

# Update frontend dependencies
cd ../frontend
npm install
```

### Rebuild Go Application

```bash
cd backend
go build -o supermarket-scraper main.go
```

### Update Node.js Dependencies

```bash
cd frontend
npm update
```

## Project Structure

```
Supermarket-scraper/
├── backend/
│   ├── main.go                  # Main application entry point
│   ├── go.mod                   # Go module dependencies
│   ├── go.sum                   # Go module checksums
│   ├── utils/
│   │   └── utils.go             # Utility functions (price calculations, parsing)
│   ├── database/
│   │   └── database.go          # SQLite database operations
│   ├── scrapers/
│   │   └── scrapers.go          # Scraper implementations using go-rod
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main React component
│   │   ├── components/
│   │   │   └── ProductCard.jsx  # Product card component
│   │   ├── main.jsx             # React entry point
│   │   └── index.css            # Tailwind CSS styles
│   ├── package.json             # Node.js dependencies
│   ├── vite.config.js           # Vite configuration
│   ├── tailwind.config.js       # Tailwind CSS configuration
│   └── Dockerfile
└── docker-compose.yml           # Docker Compose configuration
```

## Usage

1. **Open the application** in your web browser (default: `http://localhost:3100`)
2. **Enter a product name** in the search box (e.g., "cola zero", "jupiler", "milk")
3. **Click "Zoeken 🔎"** or press Enter
4. **Wait for results** - the app will scan all 10 supermarkets (takes ~10-20 seconds)
5. **Filter by size** - use the filter buttons to show only specific product sizes
6. **Compare prices** - products are sorted by price per liter/kg automatically
7. **Click on a product card** to visit the store's product page

## API Endpoints

### `GET /search`

Search for products across all supermarkets. Results are automatically saved to the database.

**Query Parameters:**
- `q` (required): Search term (minimum 2 characters)

**Example:**
```bash
curl "http://localhost:8100/search?q=cola"
```

**Response:**
```json
{
  "products": [
    {
      "store": "Colruyt",
      "name": "Coca Cola Zero 1.5L",
      "price": 1.99,
      "volume": "1.5L",
      "image": "https://...",
      "link": "https://...",
      "logo": "https://...",
      "price_per_liter": 1.33,
      "liter_value": 1.5
    }
  ],
  "scraperStatuses": [...],
  "totalElapsedTime": 12.5,
  "debugMode": false
}
```

### `GET /products`

Retrieve products from the database.

**Query Parameters:**
- `search_term` (optional): Filter by search term
- `store` (optional): Filter by store name (e.g., "Aldi", "Colruyt")
- `limit` (optional, default: 100): Maximum number of products to return (1-1000)
- `offset` (optional, default: 0): Number of products to skip for pagination

**Examples:**
```bash
# Get all products
curl "http://localhost:8100/products"

# Get products from a specific search
curl "http://localhost:8100/products?search_term=cola"

# Get products from a specific store
curl "http://localhost:8100/products?store=Aldi"

# Get products with pagination
curl "http://localhost:8100/products?limit=50&offset=100"
```

**Response:**
```json
{
  "products": [...],
  "count": 50,
  "limit": 100,
  "offset": 0
}
```

### `GET /database/stats`

Get statistics about the database.

**Example:**
```bash
curl "http://localhost:8100/database/stats"
```

**Response:**
```json
{
  "total_products": 1523,
  "products_per_store": {
    "Colruyt": 245,
    "Aldi": 189,
    "Lidl": 203,
    ...
  },
  "unique_search_terms": 45,
  "most_recent_scrape": "2025-12-28 18:45:00",
  "database_path": "products.db"
}
```

### `DELETE /database/cleanup`

Delete old products from the database.

**Query Parameters:**
- `days` (optional, default: 7): Delete products older than this many days (1-365)

**Example:**
```bash
# Delete products older than 7 days
curl -X DELETE "http://localhost:8100/database/cleanup?days=7"
```

**Response:**
```json
{
  "message": "Deleted 150 products older than 7 days",
  "deleted_count": 150
}
```

## Database

The application uses SQLite to store all scraped product information. The database file (`products.db`) is created automatically in the backend directory when you first run the application.

**Features:**
- Automatic storage of all search results
- Query products by search term, store, or get all products
- Database statistics and cleanup utilities
- Indexed for fast queries
- No external database server required

**Database Schema:**
```sql
products (
  id, store, name, price, volume, image, link,
  price_per_liter, liter_value, unit_count, unit_size, unit_type, price_per_unit,
  search_term, scraped_at, updated_at
)
```

**Configuration:**
You can configure the database path using the `DB_PATH` environment variable:
```bash
export DB_PATH=/path/to/your/database.db
uvicorn app.main:app --host 0.0.0.0 --port 8100
```

## Usage Examples

### Basic Search and Database Storage

Every search automatically saves results to the database:

```bash
# Perform a search
curl "http://localhost:8100/search?q=jupiler"

# The results are automatically saved to the database
# You can retrieve them later
curl "http://localhost:8100/products?search_term=jupiler"
```

### Querying Saved Products

```bash
# Get all products from Aldi
curl "http://localhost:8100/products?store=Aldi&limit=20"

# Get all products (with pagination)
curl "http://localhost:8100/products?limit=50&offset=0"

# Get products from multiple searches
curl "http://localhost:8100/products?search_term=cola"
curl "http://localhost:8100/products?search_term=beer"
```

### Database Maintenance

```bash
# Check database statistics
curl "http://localhost:8100/database/stats"

# Clean up old products (older than 7 days)
curl -X DELETE "http://localhost:8100/database/cleanup?days=7"

# Clean up very old products (older than 30 days)
curl -X DELETE "http://localhost:8100/database/cleanup?days=30"
```

### Using with Python

```python
import requests

# Perform a search
response = requests.get("http://localhost:8100/search?q=cola")
data = response.json()
print(f"Found {len(data['products'])} products")

# Get products from database
response = requests.get("http://localhost:8100/products?store=Colruyt")
products = response.json()['products']
for product in products[:5]:
    print(f"{product['name']} - €{product['price']}")
    
# Get database statistics
response = requests.get("http://localhost:8100/database/stats")
stats = response.json()
print(f"Total products in database: {stats['total_products']}")
print(f"Stores: {list(stats['products_per_store'].keys())}")
```

### Integration with Data Analysis

The database can be accessed directly for analysis:

```python
import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect('products.db')

# Load products into pandas DataFrame
df = pd.read_sql_query("SELECT * FROM products", conn)

# Analyze price trends
avg_prices = df.groupby('store')['price'].mean()
print(avg_prices)

# Find best deals
best_deals = df.nsmallest(10, 'price_per_liter')
print(best_deals[['store', 'name', 'price', 'price_per_liter']])

conn.close()
```

## Enhanced Scraping

### Browser Automation with go-rod/rod

All scrapers now use go-rod/rod for browser automation instead of HTTP requests with BeautifulSoup. This provides several benefits:

**Advantages:**
- ✅ **Better JavaScript handling**: Rod executes JavaScript on pages, ensuring dynamic content loads
- ✅ **More accurate scraping**: Interacts with pages like a real browser
- ✅ **Chrome DevTools Protocol**: Uses the native Chrome protocol for efficient automation
- ✅ **Concurrent scraping**: Go's goroutines enable efficient parallel scraping
- ✅ **Better debugging**: Rod provides excellent debugging capabilities
- ✅ **Headless mode**: Runs without displaying browser windows

**How it works:**
1. Rod launches a headless Chrome/Chromium browser instance
2. Each scraper navigates to the store's search results page
3. Waits for page content to load (including JavaScript)
4. Extracts product information from the DOM
5. Filters results to match the search term
6. Returns consolidated results

**Performance considerations:**
- Up to 5 concurrent browser instances run simultaneously (configurable)
- Each scraper has a timeout to prevent hanging
- Browser instances are properly cleaned up after use
- Memory efficient with proper resource management

**Which scrapers use this approach:**
- **All scrapers**: Colruyt, Albert Heijn, Aldi, Delhaize, Lidl, Jumbo, Carrefour, Prik&Tik, Snuffelstore, Drinks Corner

## Troubleshooting

### Debug Mode

**Enable Debug Mode** to see detailed logging about what URLs are being checked and why scrapers might not be returning results.

**To enable debug mode:**

```bash
# Set the DEBUG_MODE environment variable before starting the backend
export DEBUG_MODE=true
./supermarket-scraper
```

**On Windows:**
```bash
set DEBUG_MODE=true
supermarket-scraper.exe
```

**With Docker Compose:**

Add the environment variable to `docker-compose.yml`:
```yaml
backend:
  environment:
    - DEBUG_MODE=true
```

**What debug mode shows:**
- ✅ The exact URL being checked for each supermarket
- 📄 Page loading status and any errors
- 📝 Number of product elements found on each page
- ⚠️  Browser automation details and timing
- 🔍 Number of products found before and after filtering
- ⏱️ Timing information for each scraper
- 🐛 Detailed error messages with stack traces

**Example debug output:**
```
2025-12-28 20:00:00 - INFO - ============================================================
2025-12-28 20:00:00 - INFO - 🚦 NEW SEARCH REQUEST: 'cola'
2025-12-28 20:00:00 - INFO - ============================================================
2025-12-28 20:00:00 - INFO - 🛒 Colruyt: Checking https://www.collectandgo.be/nl/zoek?searchTerm=cola
2025-12-28 20:00:00 - INFO - 🔍 Starting scraper: Colruyt
2025-12-28 20:00:02 - DEBUG -   Colruyt: Page loaded successfully
2025-12-28 20:00:02 - DEBUG -   Colruyt: Found 15 product cards with selector .product-card
2025-12-28 20:00:02 - DEBUG -   Colruyt: Found 15 total results before filtering
2025-12-28 20:00:02 - DEBUG -   Colruyt: Filtered to 12 results matching 'cola'
2025-12-28 20:00:02 - INFO - ✅ Colruyt completed in 2.34s - Found 12 products
2025-12-28 20:00:10 - INFO - ============================================================
2025-12-28 20:00:10 - INFO - ✅ SEARCH COMPLETED in 10.23s
2025-12-28 20:00:10 - INFO - 📊 Total products found: 48
2025-12-28 20:00:10 - INFO - 🏪 Successful scrapers: 10/10
```

### Backend Issues

**Issue:** Port 8100 is already in use
- **Solution:** Change the port using the PORT environment variable: `PORT=8101 ./supermarket-scraper`

**Issue:** Build errors or module not found
- **Solution:** Make sure you've run `go mod download` and have Go 1.24+ installed

**Issue:** No products found for a search that should have results
- **Solution:** Enable DEBUG_MODE to see what's happening with the browser automation
- **Note:** Some websites may have changed their HTML structure or may block automated access

**Issue:** Browser/Chromium not found
- **Solution:** Install Chromium or Chrome browser on your system. Rod will automatically detect it.

### Frontend Issues

**Issue:** Port 3100 is already in use
- **Solution:** Vite will automatically use the next available port

**Issue:** Cannot connect to backend
- **Solution:** Verify the backend is running on port 8100 and update the port in `frontend/src/App.jsx` if needed

**Issue:** `npm install` fails
- **Solution:** Try deleting `node_modules` and `package-lock.json`, then run `npm install` again

### Docker Issues

**Issue:** Docker containers won't start
- **Solution:** Make sure Docker Desktop is running and ports 8100 and 3100 are available

**Issue:** Changes not reflected in Docker
- **Solution:** Rebuild the containers: `docker-compose up --build`

## Performance Notes

- Searches typically complete in 10-15 seconds with go-rod browser automation
- Up to 5 scrapers run in parallel with controlled concurrency
- Each scraper has a timeout to prevent hanging indefinitely
- Browser instances are properly cleaned up after each scrape
- Go's efficient memory management keeps resource usage low
- SQLite database provides fast local storage without external dependencies

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Commit your changes: `git commit -m 'Add some feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## License

This project is for educational purposes. Please respect the terms of service of the scraped websites.

## Support

For issues or questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the troubleshooting section above

## Acknowledgments

- Built with Go, React, go-rod/rod, and Vite
- Uses Tailwind CSS for styling
- Uses go-rod for browser automation (Chrome DevTools Protocol)
- Uses SQLite for local database storage
- Scrapes data from Belgian supermarket websites
