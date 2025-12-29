FROM golang:1.24-bookworm

WORKDIR /app

# Install runtime dependencies including Chromium
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Expose port
EXPOSE 8100

# Build and run the application
# This ensures the binary is built from the volume-mounted source code
CMD ["sh", "-c", "go mod download && CGO_ENABLED=1 go build -o supermarket-scraper main.go && ./supermarket-scraper"]
