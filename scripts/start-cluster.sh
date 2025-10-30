#!/bin/bash

# Start script for Kafka cluster with pre-flight checks

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Starting Production Kafka Cluster ===${NC}\n"

# Check Docker
echo -e "${YELLOW}Checking Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker found${NC}"

# Check Docker Compose
echo -e "${YELLOW}Checking Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose found${NC}"

# Check available memory
echo -e "\n${YELLOW}Checking available memory...${NC}"
AVAILABLE_MEM=$(free -g | awk '/^Mem:/{print $7}')
if [ "$AVAILABLE_MEM" -lt 24 ]; then
    echo -e "${YELLOW}⚠ Warning: Available memory (${AVAILABLE_MEM}GB) is less than recommended (24GB)${NC}"
    echo -e "${YELLOW}Consider reducing KAFKA_HEAP_SIZE in .env or adding more RAM${NC}"
else
    echo -e "${GREEN}✓ Sufficient memory available (${AVAILABLE_MEM}GB)${NC}"
fi

# Check disk space
echo -e "\n${YELLOW}Checking disk space...${NC}"
AVAILABLE_DISK=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$AVAILABLE_DISK" -lt 100 ]; then
    echo -e "${YELLOW}⚠ Warning: Available disk space (${AVAILABLE_DISK}GB) is less than recommended (100GB)${NC}"
else
    echo -e "${GREEN}✓ Sufficient disk space (${AVAILABLE_DISK}GB)${NC}"
fi

# Pull latest images
echo -e "\n${YELLOW}Pulling Docker images...${NC}"
docker-compose pull

# Start services
echo -e "\n${YELLOW}Starting services...${NC}"
docker-compose up -d

# Wait for ZooKeeper
echo -e "\n${YELLOW}Waiting for ZooKeeper ensemble...${NC}"
for i in {1..30}; do
    ZK_READY=0
    for z in 1 2 3; do
        STATUS=$(docker exec zookeeper-${z} bash -c "echo ruok | nc localhost 2181" 2>/dev/null || echo "failed")
        if [ "$STATUS" = "imok" ]; then
            ((ZK_READY++))
        fi
    done
    
    if [ "$ZK_READY" -eq 3 ]; then
        echo -e "${GREEN}✓ All ZooKeeper nodes ready${NC}"
        break
    fi
    
    echo -n "."
    sleep 2
done

# Wait for Kafka brokers
echo -e "\n${YELLOW}Waiting for Kafka brokers...${NC}"
for i in {1..60}; do
    KAFKA_READY=0
    for k in 1 2 3; do
        PORT=$((19091 + k))
        STATUS=$(docker exec kafka-${k} kafka-broker-api-versions --bootstrap-server localhost:${PORT} 2>/dev/null | grep -c "ApiVersion" || echo "0")
        if [ "$STATUS" -gt "0" ]; then
            ((KAFKA_READY++))
        fi
    done
    
    if [ "$KAFKA_READY" -eq 3 ]; then
        echo -e "${GREEN}✓ All Kafka brokers ready${NC}"
        break
    fi
    
    echo -n "."
    sleep 2
done

# Final status
echo -e "\n${GREEN}=== Cluster Started Successfully ===${NC}\n"
docker-compose ps

echo -e "\n${YELLOW}Access points:${NC}"
echo -e "  Kafka Brokers (external): localhost:9092, localhost:9093, localhost:9094"
echo -e "  Kafka Brokers (internal): kafka-1:19092, kafka-2:19093, kafka-3:19094"
echo -e "  Kafka UI: http://localhost:8080"
echo -e "  ZooKeeper: localhost:2181, localhost:2182, localhost:2183"

echo -e "\n${YELLOW}Next steps:${NC}"
echo -e "  1. Run health check: ./scripts/health-check.sh"
echo -e "  2. Create topics: ./scripts/create-topics.sh"
echo -e "  3. Run performance test: ./scripts/performance-test.sh"
