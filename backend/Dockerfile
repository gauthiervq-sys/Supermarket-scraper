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

# Final stage
FROM alpine:latest

WORKDIR /app

# Install runtime dependencies
RUN apk add --no-cache chromium ca-certificates

# Copy binary from builder
COPY --from=builder /build/supermarket-scraper .

# Expose port
EXPOSE 8100

# Run the application
CMD ["./supermarket-scraper"]
