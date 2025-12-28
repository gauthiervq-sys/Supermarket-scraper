# Backend - Go Implementation

This backend is written in Go and uses the go-rod/rod library for browser automation.

## Structure

```
backend/
├── main.go              # HTTP server and endpoints
├── database/            # SQLite database operations
│   └── database.go
├── scrapers/            # All scraper implementations
│   └── scrapers.go
├── utils/               # Utility functions
│   └── utils.go
├── go.mod               # Go module dependencies
├── go.sum               # Go module checksums
└── Dockerfile           # Docker configuration
```

## Building

```bash
go build -o supermarket-scraper main.go
```

## Running

```bash
# Default (port 8100)
./supermarket-scraper

# With custom port
PORT=8200 ./supermarket-scraper

# With debug mode
DEBUG_MODE=true ./supermarket-scraper

# With custom database path
DB_PATH=/path/to/database.db ./supermarket-scraper
```

## Dependencies

- **go-rod/rod**: Browser automation library (Chrome DevTools Protocol)
- **go-sqlite3**: SQLite database driver

## Features

- RESTful API with JSON responses
- Concurrent scraping (up to 5 simultaneous scrapers)
- SQLite database for product storage
- CORS enabled for frontend integration
- Debug mode for troubleshooting
- Automatic browser cleanup and resource management
