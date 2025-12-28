FROM golang:1.24-alpine AS builder

WORKDIR /build

# Install build dependencies
RUN apk add --no-cache gcc musl-dev

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build the application
RUN CGO_ENABLED=1 go build -o supermarket-scraper main.go

# Final stage - use Debian for better Chromium support
FROM debian:bookworm-slim

WORKDIR /app

# Install runtime dependencies including Chromium
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy binary from builder
COPY --from=builder /build/supermarket-scraper .

# Expose port
EXPOSE 8100

# Run the application
CMD ["./supermarket-scraper"]
