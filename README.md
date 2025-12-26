# Supermarket Scraper - BE Supermarkt Scanner Ultimate

A web application that scrapes and compares prices from multiple Belgian supermarkets in real-time. Find the best deals on products across Colruyt, Albert Heijn, Aldi, Delhaize, Lidl, Jumbo, Carrefour, Prik&Tik, Snuffelstore, and Drinks Corner.

## Features

- 🔍 Real-time product search across 10 Belgian supermarkets
- 💰 Price comparison with price-per-liter/kg calculations
- 🏪 Store logos and product images
- 📊 Filter results by product size/volume
- ⚡ Parallel scraping for faster results
- 🎨 Modern, responsive UI with dark mode

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
- **Node.js 16+** and **npm** - [Download Node.js](https://nodejs.org/)
- **Git** - [Download Git](https://git-scm.com/downloads/)

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

The frontend will be available at `http://localhost:5173` (or another port if 5173 is busy)

### Option 2: Docker Compose (Easiest)

If you have Docker installed, you can run everything with one command:

```bash
# From the project root directory
docker-compose up --build
```

This will:
- Build and start the backend on port 8100
- Build and start the frontend on port 5173
- Handle all dependencies automatically

Access the application at `http://localhost:5173`

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

1. **Open the application** in your web browser (default: `http://localhost:5173`)
2. **Enter a product name** in the search box (e.g., "cola zero", "jupiler", "milk")
3. **Click "Zoeken 🔎"** or press Enter
4. **Wait for results** - the app will scan all 10 supermarkets (takes ~10-20 seconds)
5. **Filter by size** - use the filter buttons to show only specific product sizes
6. **Compare prices** - products are sorted by price per liter/kg automatically
7. **Click on a product card** to visit the store's product page

## API Endpoints

### `GET /search`

Search for products across all supermarkets.

**Query Parameters:**
- `q` (required): Search term (minimum 2 characters)

**Example:**
```bash
curl "http://localhost:8100/search?q=cola"
```

**Response:**
```json
[
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
]
```

## Troubleshooting

### Backend Issues

**Issue:** `playwright: command not found`
- **Solution:** Run `playwright install chromium` after installing requirements

**Issue:** Port 8100 is already in use
- **Solution:** Change the port in the uvicorn command: `--port 8101`

**Issue:** Import errors or module not found
- **Solution:** Make sure you're in the virtual environment and have installed all requirements

### Frontend Issues

**Issue:** Port 5173 is already in use
- **Solution:** Vite will automatically use the next available port

**Issue:** Cannot connect to backend
- **Solution:** Verify the backend is running on port 8100 and update the port in `frontend/src/App.jsx` if needed

**Issue:** `npm install` fails
- **Solution:** Try deleting `node_modules` and `package-lock.json`, then run `npm install` again

### Docker Issues

**Issue:** Docker containers won't start
- **Solution:** Make sure Docker Desktop is running and ports 8100 and 5173 are available

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
