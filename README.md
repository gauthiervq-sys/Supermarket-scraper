# Supermarket Scraper - BE Supermarkt Scanner Ultimate

A web application that scrapes and compares prices from multiple Belgian supermarkets in real-time. Find the best deals on products across Colruyt, Albert Heijn, Aldi, Delhaize, Lidl, Jumbo, Carrefour, Prik&Tik, Snuffelstore, and Drinks Corner.

## Features

- 🔍 Real-time product search across 10 Belgian supermarkets
- 💰 Price comparison with price-per-liter/kg calculations
- 🏪 Store logos and product images
- 📊 Filter results by product size/volume
- ⚡ Parallel scraping for faster results
- 🎨 Modern, responsive UI with dark mode
- 🐛 **Debug mode** to see what sites are being checked and troubleshoot scraping issues
- 💾 **Database storage** - All scraped products are automatically saved to a database
- 🔗 **Enhanced scraping** - Visits individual product pages for more complete information

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
- **Node.js 16+** and **npm** - [Download Node.js](https://nodejs.org/)
- **Git** - [Download Git](https://git-scm.com/downloads/)
- **Tesseract OCR** - Required for extracting prices from images
  - **Windows**: Download from [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) or use `choco install tesseract`
  - **macOS**: `brew install tesseract`
  - **Linux (Ubuntu/Debian)**: `sudo apt-get install tesseract-ocr`

Optional (for containerized deployment):
- **Docker** and **Docker Compose** - [Download Docker](https://www.docker.com/get-started)

## Installation from Scratch

### 1. Clone the Repository

```bash
git clone https://github.com/gauthiervq-sys/Supermarket-scraper.git
cd Supermarket-scraper
```

### 2. Backend Setup

Navigate to the backend directory and set up the Python environment:

```bash
cd backend

# Create a virtual environment (recommended)
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers (required for web scraping)
playwright install chromium
```

**Note**: The application uses OCR (Optical Character Recognition) to extract prices from websites that embed prices in images. Make sure Tesseract OCR is installed on your system (see Prerequisites above).

### 3. Frontend Setup

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

# Activate virtual environment if not already activated
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Run the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8100 --reload
```

The backend API will be available at `http://localhost:8100`

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
pip install -r requirements.txt --upgrade

# Update frontend dependencies
cd ../frontend
npm install
```

### Update Python Dependencies

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt --upgrade
```

### Update Node.js Dependencies

```bash
cd frontend
npm update
```

### Update Playwright Browsers

```bash
playwright install chromium
```

## Project Structure

```
Supermarket-scraper/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── utils.py             # Utility functions (price calculations)
│   │   └── scrapers/            # Individual scraper modules
│   │       ├── colruyt.py
│   │       ├── ah.py
│   │       ├── aldi.py
│   │       ├── delhaize.py
│   │       ├── lidl.py
│   │       ├── jumbo.py
│   │       ├── carrefour.py
│   │       ├── prikentik.py
│   │       └── small_shops.py
│   ├── requirements.txt         # Python dependencies
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

### Individual Product Page Visits

Some scrapers (Aldi, Prik&Tik) have been enhanced to visit individual product pages instead of only scraping search results. This provides several benefits:

**Advantages:**
- ✅ **Better price accuracy**: Prices on product pages are often displayed as text rather than images
- ✅ **More complete information**: Product pages contain detailed specifications
- ✅ **Avoids OCR complexity**: No need to extract prices from images using OCR
- ✅ **More reliable data**: Less prone to changes in search result page layouts

**How it works:**
1. Scraper visits the search results page
2. Collects all product links
3. Visits each product detail page
4. Extracts complete product information
5. Returns consolidated results

**Performance considerations:**
- Individual page visits increase scraping time (but still within acceptable limits)
- Parallel processing helps maintain reasonable speed
- Timeout settings ensure scrapers don't hang indefinitely

**Which scrapers use this approach:**
- **Aldi**: Visits product detail pages for complete info
- **Prik&Tik**: Visits product detail pages to avoid image-based prices
- **Colruyt, AH, Lidl, Delhaize**: Use API interception (already optimal)

## Troubleshooting

### Debug Mode

**Enable Debug Mode** to see detailed logging about what URLs are being checked and why scrapers might not be returning results.

**To enable debug mode:**

```bash
# Set the DEBUG_MODE environment variable before starting the backend
export DEBUG_MODE=true
uvicorn app.main:app --host 0.0.0.0 --port 8100 --reload
```

**On Windows:**
```bash
set DEBUG_MODE=true
uvicorn app.main:app --host 0.0.0.0 --port 8100 --reload
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
- 🔍 Number of products found before and after filtering
- ⏱️ Timing information for each scraper
- 🐛 Detailed error messages with stack traces
- 📊 API response interceptions and parsing details

**Example debug output:**
```
2025-12-27 19:47:27,334 - app.main - INFO - ============================================================
2025-12-27 19:47:27,334 - app.main - INFO - 🚦 NEW SEARCH REQUEST: 'cola'
2025-12-27 19:47:27,334 - app.main - INFO - ============================================================
2025-12-27 19:47:27,335 - app.scrapers.colruyt - INFO - 🛒 Colruyt: Checking https://www.collectandgo.be/nl/zoek?searchTerm=cola
2025-12-27 19:47:27,335 - app.scrapers.ah - INFO - 🛒 Albert Heijn: Checking https://www.ah.be/zoeken?query=cola
2025-12-27 19:47:28,633 - app.scrapers.colruyt - DEBUG -   Colruyt: Found 15 total results before filtering
2025-12-27 19:47:28,633 - app.scrapers.colruyt - DEBUG -   Colruyt: Filtered to 12 results matching 'cola'
2025-12-27 19:47:29,446 - app.main - INFO - ============================================================
2025-12-27 19:47:29,446 - app.main - INFO - ✅ SEARCH COMPLETED in 2.11s
2025-12-27 19:47:29,446 - app.main - INFO - 📊 Total products found: 48
2025-12-27 19:47:29,446 - app.main - INFO - 🏪 Successful scrapers: 10/10
```

### Backend Issues

**Issue:** `playwright: command not found`
- **Solution:** Run `playwright install chromium` after installing requirements

**Issue:** Port 8100 is already in use
- **Solution:** Change the port in the uvicorn command: `--port 8101`

**Issue:** Import errors or module not found
- **Solution:** Make sure you're in the virtual environment and have installed all requirements

**Issue:** No products found for a search that should have results
- **Solution:** Enable DEBUG_MODE to see what URLs are being checked and what errors might be occurring

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

- Initial searches may take 15-20 seconds as the scrapers visit each store
- Scrapers run in parallel with a maximum of 3 concurrent browsers to prevent overwhelming the system
- Some stores may timeout or fail occasionally due to network issues or website changes
- Playwright headless browsers are used for most scrapers; Jumbo uses API calls for better performance

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

- Built with FastAPI, React, Playwright, and Vite
- Uses Tailwind CSS for styling
- Scrapes data from Belgian supermarket websites
