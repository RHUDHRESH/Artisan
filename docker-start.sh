#!/bin/bash
# Artisan Hub - Docker Startup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Artisan Hub - Docker Deployment${NC}"
echo "=================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Creating from .env.example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env file. Please configure it with your API keys.${NC}"
    else
        echo -e "${RED}❌ .env.example not found!${NC}"
        exit 1
    fi
fi

# Parse command line arguments
MODE=${1:-prod}  # Default to production

case $MODE in
    dev)
        echo -e "${GREEN}Starting in DEVELOPMENT mode...${NC}"
        docker-compose -f docker-compose.dev.yml up --build
        ;;
    prod)
        echo -e "${GREEN}Starting in PRODUCTION mode...${NC}"
        docker-compose -f docker-compose.yml up -d --build
        echo -e "${GREEN}✅ Services started!${NC}"
        echo ""
        echo "Access the application at:"
        echo "  Frontend: http://localhost:3000"
        echo "  Backend:  http://localhost:8000"
        echo "  API Docs: http://localhost:8000/docs"
        echo ""
        echo "To view logs: docker-compose logs -f"
        echo "To stop: docker-compose down"
        ;;
    stop)
        echo -e "${YELLOW}Stopping all services...${NC}"
        docker-compose -f docker-compose.yml down
        docker-compose -f docker-compose.dev.yml down
        echo -e "${GREEN}✅ Services stopped${NC}"
        ;;
    logs)
        echo -e "${GREEN}Showing logs (Ctrl+C to exit)...${NC}"
        docker-compose -f docker-compose.yml logs -f
        ;;
    *)
        echo "Usage: $0 {dev|prod|stop|logs}"
        echo ""
        echo "  dev   - Start in development mode with hot reload"
        echo "  prod  - Start in production mode (default)"
        echo "  stop  - Stop all services"
        echo "  logs  - View logs"
        exit 1
        ;;
esac
