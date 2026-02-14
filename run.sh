#!/bin/bash

echo "================================================"
echo "  🦎 LizardTail - Self-Healing System Launcher"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Clean up
echo -e "${YELLOW}[1/5] Cleaning up old containers...${NC}"
docker compose down --remove-orphans 2>/dev/null
docker rm -f $(docker ps -aq --filter "name=lizardtail") 2>/dev/null
echo -e "${GREEN}✓ Cleanup complete${NC}"
echo ""

# Step 2: Build images
echo -e "${YELLOW}[2/5] Building Docker images...${NC}"
docker compose build
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Build complete${NC}"
echo ""

# Step 3: Start services
echo -e "${YELLOW}[3/5] Starting services...${NC}"
docker compose up -d
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to start services${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Services started${NC}"
echo ""

# Step 4: Wait for services to be ready
echo -e "${YELLOW}[4/5] Waiting for services to be ready...${NC}"
sleep 5

# Check service_a
for i in {1..10}; do
    if curl -s http://localhost:5000/health > /dev/null; then
        echo -e "${GREEN}✓ service_a is ready${NC}"
        break
    fi
    echo "  Waiting for service_a... ($i/10)"
    sleep 2
done

# Check orchestrator
for i in {1..10}; do
    if curl -s http://localhost:8000/status > /dev/null; then
        echo -e "${GREEN}✓ orchestrator is ready${NC}"
        break
    fi
    echo "  Waiting for orchestrator... ($i/10)"
    sleep 2
done

echo ""

# Step 5: Open dashboard
echo -e "${YELLOW}[5/5] Launching dashboard...${NC}"
echo ""
echo "================================================"
echo -e "${GREEN}✓ System is running!${NC}"
echo "================================================"
echo ""
echo "Access points:"
echo "  🌐 Dashboard:        file://$(pwd)/dashboard/index.html"
echo "  🔧 Orchestrator:     http://localhost:8000/status"
echo "  🌡️  Service A:        http://localhost:5000/sensor"
echo "  📦 Service B:        http://localhost:5001/status"
echo ""
echo "Commands:"
echo "  View logs:           docker-compose logs -f"
echo "  Stop system:         docker-compose down"
echo "  Restart:             docker-compose restart"
echo ""
echo "Opening dashboard in browser..."
echo ""

# Try to open dashboard in default browser
if command -v xdg-open > /dev/null; then
    xdg-open "dashboard/index.html"
elif command -v open > /dev/null; then
    open "dashboard/index.html"
elif command -v start > /dev/null; then
    start "dashboard/index.html"
else
    echo "Please open dashboard/index.html manually in your browser"
fi

echo -e "${GREEN}🦎 LizardTail is ready for action!${NC}"
