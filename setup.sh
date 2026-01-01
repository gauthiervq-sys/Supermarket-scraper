#!/usr/bin/env bash

# Supermarket Scraper Setup Script
# This script automates the installation and setup process

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ${NC}  $1"
}

print_success() {
    echo -e "${GREEN}✓${NC}  $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

print_error() {
    echo -e "${RED}✗${NC}  $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Print header
echo "========================================"
echo "  Supermarket Scraper Setup"
echo "========================================"
echo ""

# Check if we're already in the repo
if [ -f "docker-compose.yml" ] && [ -d "backend" ] && [ -d "frontend" ]; then
    print_info "Already in Supermarket-scraper directory"
    REPO_DIR="$(pwd)"
else
    # Check if Git is installed
    if ! command_exists git; then
        print_error "Git is not installed. Please install Git first."
        echo "  Visit: https://git-scm.com/downloads"
        exit 1
    fi
    print_success "Git is installed"

    # Clone the repository
    print_info "Cloning the repository..."
    if [ -d "Supermarket-scraper" ]; then
        print_warning "Directory 'Supermarket-scraper' already exists. Using existing directory."
        cd Supermarket-scraper
    else
        git clone https://github.com/gauthiervq-sys/Supermarket-scraper.git
        cd Supermarket-scraper
        print_success "Repository cloned successfully"
    fi
    REPO_DIR="$(pwd)"
fi

echo ""
echo "========================================"
echo "  Checking Prerequisites"
echo "========================================"
echo ""

# Check for Go
if ! command_exists go; then
    print_error "Go is not installed. Please install Go 1.24 or later."
    echo "  Visit: https://golang.org/dl/"
    exit 1
fi
GO_VERSION=$(go version | awk '{print $3}' | sed 's/go//')
print_success "Go $GO_VERSION is installed"

# Check for Node.js
if ! command_exists node; then
    print_error "Node.js is not installed. Please install Node.js 16 or later."
    echo "  Visit: https://nodejs.org/"
    exit 1
fi
NODE_VERSION=$(node --version)
print_success "Node.js $NODE_VERSION is installed"

# Check for npm
if ! command_exists npm; then
    print_error "npm is not installed. Please install npm."
    exit 1
fi
NPM_VERSION=$(npm --version)
print_success "npm $NPM_VERSION is installed"

echo ""
echo "========================================"
echo "  Setting up Backend (Go)"
echo "========================================"
echo ""

cd "$REPO_DIR/backend"

print_info "Downloading Go dependencies..."
go mod download
print_success "Go dependencies downloaded"

print_info "Building backend..."
go build -o supermarket-scraper main.go
print_success "Backend built successfully"

echo ""
echo "========================================"
echo "  Setting up Frontend (Node.js)"
echo "========================================"
echo ""

cd "$REPO_DIR/frontend"

print_info "Installing Node.js dependencies..."
npm install
print_success "Node.js dependencies installed"

echo ""
echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
print_success "Supermarket Scraper has been set up successfully!"
echo ""
echo "To run the application:"
echo ""
echo "  Option 1: Run with Docker Compose (recommended)"
echo "    ${GREEN}cd $REPO_DIR${NC}"
echo "    ${GREEN}docker-compose up --build${NC}"
echo "    Access at: ${BLUE}http://localhost:3100${NC}"
echo ""
echo "  Option 2: Run manually (two terminals required)"
echo ""
echo "    Terminal 1 - Backend:"
echo "      ${GREEN}cd $REPO_DIR/backend${NC}"
echo "      ${GREEN}./supermarket-scraper${NC}"
echo ""
echo "    Terminal 2 - Frontend:"
echo "      ${GREEN}cd $REPO_DIR/frontend${NC}"
echo "      ${GREEN}npm run dev${NC}"
echo ""
echo "    Access at: ${BLUE}http://localhost:3100${NC}"
echo ""
echo "For more information, see README.md"
echo ""
