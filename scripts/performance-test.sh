#!/bin/bash

# Performance testing script for Kafka cluster
# Tests producer and consumer throughput

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

BOOTSTRAP_SERVERS="kafka-1:19092,kafka-2:19093,kafka-3:19094"
TEST_TOPIC="performance-test-topic"
NUM_RECORDS=10000
RECORD_SIZE=102400  # 100KB as per handbook target
THROUGHPUT=1000     # Target 1000 msgs/sec

echo -e "${GREEN}=== Kafka Performance Test ===${NC}\n"

# Create test topic if it doesn't exist
echo -e "${YELLOW}Creating test topic...${NC}"
docker exec kafka-1 kafka-topics --create \
    --bootstrap-server ${BOOTSTRAP_SERVERS} \
    --topic ${TEST_TOPIC} \
    --partitions 12 \
    --replication-factor 3 \
    --config min.insync.replicas=2 \
    --config compression.type=lz4 \
    --if-not-exists 2>/dev/null || true

echo -e "${GREEN}✓ Test topic ready${NC}\n"

# Producer Performance Test
echo -e "${YELLOW}=== Producer Performance Test ===${NC}"
echo -e "Target: ${THROUGHPUT} msgs/sec @ ${RECORD_SIZE} bytes (~100 MB/s)\n"

docker exec kafka-1 kafka-producer-perf-test \
    --topic ${TEST_TOPIC} \
    --num-records ${NUM_RECORDS} \
    --record-size ${RECORD_SIZE} \
    --throughput ${THROUGHPUT} \
    --producer-props \
        bootstrap.servers=${BOOTSTRAP_SERVERS} \
        acks=all \
        compression.type=lz4 \
        linger.ms=100 \
        batch.size=1048576 \
        buffer.memory=67108864

echo -e "\n${YELLOW}=== Consumer Performance Test ===${NC}\n"

# Consumer Performance Test
docker exec kafka-1 kafka-consumer-perf-test \
    --topic ${TEST_TOPIC} \
    --bootstrap-server ${BOOTSTRAP_SERVERS} \
    --messages ${NUM_RECORDS} \
    --threads 12 \
    --group perf-test-consumer-group \
    --show-detailed-stats

echo -e "\n${GREEN}=== Performance Test Complete ===${NC}"
echo -e "${YELLOW}Note: Results depend on available resources. For production, ensure adequate CPU, memory, and disk I/O.${NC}"

# Cleanup option
echo -e "\n${YELLOW}Delete test topic? (y/N)${NC}"
read -t 10 -n 1 CLEANUP || CLEANUP="n"
echo ""
if [ "$CLEANUP" = "y" ] || [ "$CLEANUP" = "Y" ]; then
    docker exec kafka-1 kafka-topics --delete \
        --bootstrap-server ${BOOTSTRAP_SERVERS} \
        --topic ${TEST_TOPIC}
    echo -e "${GREEN}✓ Test topic deleted${NC}"
fi
