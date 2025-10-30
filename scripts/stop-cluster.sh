#!/bin/bash

# Stop script for Kafka cluster with graceful shutdown

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}=== Stopping Kafka Cluster ===${NC}\n"

# Check if cluster is running
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${YELLOW}Cluster is not running${NC}"
    exit 0
fi

# Graceful shutdown
echo -e "${YELLOW}Performing graceful shutdown...${NC}"
docker-compose stop

echo -e "${GREEN}✓ All services stopped${NC}"

# Ask about removing containers
echo -e "\n${YELLOW}Remove containers? (y/N)${NC}"
read -t 10 -n 1 REMOVE_CONTAINERS || REMOVE_CONTAINERS="n"
echo ""

if [ "$REMOVE_CONTAINERS" = "y" ] || [ "$REMOVE_CONTAINERS" = "Y" ]; then
    docker-compose down
    echo -e "${GREEN}✓ Containers removed${NC}"
    
    # Ask about removing volumes
    echo -e "\n${RED}Remove volumes (DATA LOSS!)? (y/N)${NC}"
    read -t 10 -n 1 REMOVE_VOLUMES || REMOVE_VOLUMES="n"
    echo ""
    
    if [ "$REMOVE_VOLUMES" = "y" ] || [ "$REMOVE_VOLUMES" = "Y" ]; then
        docker-compose down -v
        echo -e "${RED}✓ Volumes removed (all data deleted)${NC}"
    fi
fi

echo -e "\n${GREEN}=== Shutdown Complete ===${NC}"
