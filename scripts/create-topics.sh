#!/bin/bash

# Script to create production-ready Kafka topics
# Based on the handbook recommendations

set -e

BOOTSTRAP_SERVERS="kafka-1:19092,kafka-2:19093,kafka-3:19094"
REPLICATION_FACTOR=3
MIN_INSYNC_REPLICAS=2

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Creating production Kafka topics...${NC}"

# Function to create topic
create_topic() {
    local TOPIC_NAME=$1
    local PARTITIONS=$2
    local RETENTION_MS=${3:-604800000} # Default 7 days
    
    echo -e "${YELLOW}Creating topic: ${TOPIC_NAME} with ${PARTITIONS} partitions...${NC}"
    
    docker exec kafka-1 kafka-topics --create \
        --bootstrap-server ${BOOTSTRAP_SERVERS} \
        --topic ${TOPIC_NAME} \
        --partitions ${PARTITIONS} \
        --replication-factor ${REPLICATION_FACTOR} \
        --config min.insync.replicas=${MIN_INSYNC_REPLICAS} \
        --config compression.type=lz4 \
        --config retention.ms=${RETENTION_MS} \
        --config segment.ms=600000 \
        --config max.message.bytes=1048576 \
        --if-not-exists
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Topic ${TOPIC_NAME} created successfully${NC}"
    else
        echo -e "${RED}✗ Failed to create topic ${TOPIC_NAME}${NC}"
    fi
}

# Example topics for different use cases

# High-throughput topic (12 partitions = 3 brokers × 4 cores)
create_topic "high-throughput-events" 12 604800000

# Medium-throughput topic
create_topic "medium-throughput-events" 6 604800000

# Low-latency topic (fewer partitions for lower latency)
create_topic "low-latency-commands" 3 86400000

# Long retention topic (30 days)
create_topic "audit-logs" 12 2592000000

# Compacted topic (for changelog/state)
docker exec kafka-1 kafka-topics --create \
    --bootstrap-server ${BOOTSTRAP_SERVERS} \
    --topic "user-state-changelog" \
    --partitions 6 \
    --replication-factor ${REPLICATION_FACTOR} \
    --config min.insync.replicas=${MIN_INSYNC_REPLICAS} \
    --config cleanup.policy=compact \
    --config compression.type=lz4 \
    --config segment.ms=600000 \
    --config min.cleanable.dirty.ratio=0.5 \
    --if-not-exists

echo -e "${GREEN}✓ All topics created successfully${NC}"

# List all topics
echo -e "\n${YELLOW}Current topics:${NC}"
docker exec kafka-1 kafka-topics --list --bootstrap-server ${BOOTSTRAP_SERVERS}

# Describe topics
echo -e "\n${YELLOW}Topic details:${NC}"
docker exec kafka-1 kafka-topics --describe --bootstrap-server ${BOOTSTRAP_SERVERS}
