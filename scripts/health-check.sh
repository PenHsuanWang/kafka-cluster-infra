#!/bin/bash

# Health check script for Kafka cluster
# Verifies all components are running correctly

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Kafka Cluster Health Check ===${NC}\n"

# Check Docker Compose services
echo -e "${YELLOW}1. Checking Docker services...${NC}"
docker-compose ps

# Check ZooKeeper ensemble
echo -e "\n${YELLOW}2. Checking ZooKeeper ensemble...${NC}"
for i in 1 2 3; do
    STATUS=$(docker exec zookeeper-${i} bash -c "echo ruok | nc localhost 2181" 2>/dev/null || echo "failed")
    if [ "$STATUS" = "imok" ]; then
        echo -e "${GREEN}✓ ZooKeeper-${i}: OK${NC}"
    else
        echo -e "${RED}✗ ZooKeeper-${i}: FAILED${NC}"
    fi
done

# Check Kafka brokers
echo -e "\n${YELLOW}3. Checking Kafka brokers...${NC}"
for i in 1 2 3; do
    BROKER_ID=$i
    PORT=$((19091 + i))
    
    BROKER_STATUS=$(docker exec kafka-${i} kafka-broker-api-versions --bootstrap-server localhost:${PORT} 2>/dev/null | grep -c "ApiVersion" || echo "0")
    
    if [ "$BROKER_STATUS" -gt "0" ]; then
        echo -e "${GREEN}✓ Kafka-${i}: OK (listening on port ${PORT})${NC}"
    else
        echo -e "${RED}✗ Kafka-${i}: FAILED${NC}"
    fi
done

# Check cluster metadata
echo -e "\n${YELLOW}4. Checking cluster metadata...${NC}"
docker exec kafka-1 kafka-metadata --bootstrap-server kafka-1:19092,kafka-2:19093,kafka-3:19094 --describe --all 2>/dev/null || echo "Metadata check skipped (requires newer Kafka version)"

# Check for under-replicated partitions
echo -e "\n${YELLOW}5. Checking for under-replicated partitions...${NC}"
UNDER_REPLICATED=$(docker exec kafka-1 kafka-topics --describe --bootstrap-server kafka-1:19092 --under-replicated-partitions 2>/dev/null | grep -c "Topic:" || echo "0")

if [ "$UNDER_REPLICATED" -eq "0" ]; then
    echo -e "${GREEN}✓ No under-replicated partitions${NC}"
else
    echo -e "${RED}✗ Found ${UNDER_REPLICATED} under-replicated partition(s)${NC}"
    docker exec kafka-1 kafka-topics --describe --bootstrap-server kafka-1:19092 --under-replicated-partitions
fi

# Check topic list
echo -e "\n${YELLOW}6. Listing topics...${NC}"
docker exec kafka-1 kafka-topics --list --bootstrap-server kafka-1:19092

# Check consumer groups
echo -e "\n${YELLOW}7. Listing consumer groups...${NC}"
GROUPS=$(docker exec kafka-1 kafka-consumer-groups --list --bootstrap-server kafka-1:19092 2>/dev/null || echo "")
if [ -z "$GROUPS" ]; then
    echo "No consumer groups found"
else
    echo "$GROUPS"
fi

# Check disk usage
echo -e "\n${YELLOW}8. Checking disk usage...${NC}"
docker exec kafka-1 df -h /var/lib/kafka/data | tail -1
docker exec kafka-2 df -h /var/lib/kafka/data | tail -1
docker exec kafka-3 df -h /var/lib/kafka/data | tail -1

# Check container resource usage
echo -e "\n${YELLOW}9. Container resource usage:${NC}"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" kafka-1 kafka-2 kafka-3

echo -e "\n${GREEN}=== Health Check Complete ===${NC}"
echo -e "${YELLOW}For detailed monitoring, visit Kafka UI at http://localhost:8080${NC}"
