#!/bin/bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   Kafka Cluster Stress Test Suite${NC}"
echo -e "${GREEN}============================================${NC}\n"

# Detect if testing remote or local cluster
if [ -z "$KAFKA_BROKERS" ]; then
    echo -e "${BLUE}Mode: LOCAL (localhost)${NC}"
    echo -e "${YELLOW}To test remote cluster, set: export KAFKA_BROKERS=\"host1:9092,host2:9092,host3:9092\"${NC}\n"
    USE_LOCAL=true
else
    echo -e "${BLUE}Mode: REMOTE${NC}"
    echo -e "${BLUE}Kafka Brokers: ${KAFKA_BROKERS}${NC}\n"
    USE_LOCAL=false
fi

# Setup Python environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo -e "\n${GREEN}✓ Environment ready${NC}\n"

# Create test topic
echo -e "${YELLOW}Creating test topic...${NC}"

if [ "$USE_LOCAL" = true ]; then
    # Local cluster: use docker exec
    docker exec kafka-1 kafka-topics --create \
      --bootstrap-server kafka-1:19092 \
      --topic ${TEST_TOPIC:-stress-test-topic} \
      --partitions ${TOPIC_PARTITIONS:-12} \
      --replication-factor ${TOPIC_REPLICATION_FACTOR:-3} \
      --config min.insync.replicas=${TOPIC_MIN_ISR:-2} \
      --config compression.type=lz4 \
      --if-not-exists 2>/dev/null || true
else
    # Remote cluster: use kafka-topics from local kafka installation or skip
    if command -v kafka-topics.sh &> /dev/null || command -v kafka-topics &> /dev/null; then
        KAFKA_CMD=$(command -v kafka-topics.sh || command -v kafka-topics)
        $KAFKA_CMD --create \
          --bootstrap-server ${KAFKA_BROKERS} \
          --topic ${TEST_TOPIC:-stress-test-topic} \
          --partitions ${TOPIC_PARTITIONS:-12} \
          --replication-factor ${TOPIC_REPLICATION_FACTOR:-3} \
          --config min.insync.replicas=${TOPIC_MIN_ISR:-2} \
          --config compression.type=lz4 \
          --if-not-exists 2>/dev/null || true
    else
        echo -e "${YELLOW}⚠ kafka-topics command not found. Skipping topic creation.${NC}"
        echo -e "${YELLOW}  Please create topic '${TEST_TOPIC:-stress-test-topic}' manually on remote cluster.${NC}"
    fi
fi

echo -e "${GREEN}✓ Topic ready${NC}\n"

# Run producer test
echo -e "${YELLOW}Running producer stress test...${NC}"
echo -e "${YELLOW}Sending 100,000 messages (10 producers × 10,000)${NC}\n"
python3 producer_stress.py

echo -e "\n${GREEN}✓ Producer test complete${NC}\n"

# Run consumer test
echo -e "${YELLOW}Running consumer stress test...${NC}"
echo -e "${YELLOW}Consuming with 15 consumers (5 groups × 3)${NC}\n"
python3 consumer_stress.py

echo -e "\n${GREEN}✓ Consumer test complete${NC}\n"

# Generate report
echo -e "${YELLOW}Generating performance report...${NC}"
python3 report_generator.py

echo -e "\n${GREEN}============================================${NC}"
echo -e "${GREEN}   Stress Test Complete!${NC}"
echo -e "${GREEN}============================================${NC}\n"

echo -e "Results: ${YELLOW}test-results/STRESS_TEST_REPORT.md${NC}\n"

# Show summary
if [ -f "test-results/producer_results.json" ]; then
    echo -e "${GREEN}Quick Summary:${NC}"
    python3 -c "
import json
with open('test-results/producer_results.json') as f:
    p = json.load(f)
    print(f'  Producer: {p.get(\"total_messages_sent\", 0):,} msgs @ {p.get(\"throughput_mb_per_sec\", 0):.2f} MB/s')
    print(f'  Success: {p.get(\"success_rate\", 0)*100:.2f}%')
with open('test-results/consumer_results.json') as f:
    c = json.load(f)
    print(f'  Consumer: {c.get(\"total_messages_consumed\", 0):,} msgs @ {c.get(\"throughput_mb_per_sec\", 0):.2f} MB/s')
    print(f'  End-to-End P99: {c.get(\"p99_latency_ms\", 0):.2f} ms')
"
fi

echo -e "\n${YELLOW}Cleanup:${NC}"
if [ "$USE_LOCAL" = true ]; then
    echo -e "  docker exec kafka-1 kafka-topics --delete --bootstrap-server kafka-1:19092 --topic ${TEST_TOPIC:-stress-test-topic}\n"
else
    echo -e "  kafka-topics.sh --delete --bootstrap-server ${KAFKA_BROKERS} --topic ${TEST_TOPIC:-stress-test-topic}\n"
fi

deactivate
