FROM golang:1.24-bookworm

WORKDIR /app

# Install runtime dependencies including Chromium
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Pre-download modules during build to speed up startup
# Copy go.mod and go.sum first for better layer caching
COPY go.mod go.sum ./
RUN go mod download

# Expose port
EXPOSE 8100

# Build and run the application from volume-mounted source
CMD ["sh", "-c", "CGO_ENABLED=1 go build -o supermarket-scraper main.go && ./supermarket-scraper"]
