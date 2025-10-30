#!/bin/bash
#
# Helper script for testing remote Kafka clusters
# Usage: ./test-remote.sh <broker1:port> <broker2:port> <broker3:port>
#
# Example: ./test-remote.sh vm1:9092 vm2:9092 vm3:9092
#

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if broker addresses provided
if [ $# -lt 1 ]; then
    echo -e "${RED}Error: No broker addresses provided${NC}"
    echo ""
    echo "Usage: $0 <broker1:port> [broker2:port] [broker3:port] ..."
    echo ""
    echo "Examples:"
    echo "  $0 vm1:9092 vm2:9092 vm3:9092"
    echo "  $0 10.0.1.10:9092 10.0.1.11:9092 10.0.1.12:9092"
    echo "  $0 kafka1.example.com:9092 kafka2.example.com:9092"
    echo ""
    exit 1
fi

# Build broker list
BROKERS=""
for broker in "$@"; do
    if [ -z "$BROKERS" ]; then
        BROKERS="$broker"
    else
        BROKERS="$BROKERS,$broker"
    fi
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Remote Kafka Cluster Test${NC}"
echo -e "${BLUE}========================================${NC}\n"
echo -e "${GREEN}Brokers: ${BROKERS}${NC}\n"

# Test connectivity
echo -e "${YELLOW}Testing connectivity to brokers...${NC}\n"
ALL_REACHABLE=true
for broker in "$@"; do
    host=$(echo $broker | cut -d: -f1)
    port=$(echo $broker | cut -d: -f2)
    
    if command -v nc &> /dev/null; then
        if nc -zv -w5 $host $port 2>&1 | grep -q "succeeded\|open\|Connected"; then
            echo -e "  ${GREEN}✓${NC} $broker reachable"
        else
            echo -e "  ${RED}✗${NC} $broker NOT reachable"
            ALL_REACHABLE=false
        fi
    elif command -v telnet &> /dev/null; then
        if timeout 5 telnet $host $port 2>&1 | grep -q "Connected\|Escape"; then
            echo -e "  ${GREEN}✓${NC} $broker reachable"
        else
            echo -e "  ${RED}✗${NC} $broker NOT reachable"
            ALL_REACHABLE=false
        fi
    else
        echo -e "  ${YELLOW}⚠${NC} Cannot test connectivity (nc/telnet not found)"
        break
    fi
done

if [ "$ALL_REACHABLE" = false ]; then
    echo -e "\n${RED}Error: Some brokers are not reachable. Please check:${NC}"
    echo "  1. Network connectivity"
    echo "  2. Firewall rules"
    echo "  3. Broker addresses and ports"
    exit 1
fi

echo -e "\n${GREEN}All brokers reachable!${NC}\n"

# Test Kafka connection
echo -e "${YELLOW}Testing Kafka connection...${NC}\n"
if python3 -c "
from confluent_kafka.admin import AdminClient
import sys
try:
    admin = AdminClient({'bootstrap.servers': '$BROKERS', 'socket.timeout.ms': 10000})
    metadata = admin.list_topics(timeout=10)
    print(f'✓ Successfully connected to Kafka cluster')
    print(f'  Brokers: {len(metadata.brokers)}')
    for broker in metadata.brokers.values():
        print(f'    - Broker {broker.id}: {broker.host}:{broker.port}')
    print(f'  Topics: {len(metadata.topics)}')
    sys.exit(0)
except Exception as e:
    print(f'✗ Failed to connect: {e}')
    sys.exit(1)
" 2>/dev/null; then
    echo ""
else
    echo -e "${RED}Failed to connect to Kafka cluster${NC}"
    echo "Please verify:"
    echo "  1. Broker advertised.listeners configuration"
    echo "  2. Security settings (SASL/SSL if enabled)"
    exit 1
fi

# Run stress test
echo -e "${YELLOW}Starting stress test...${NC}\n"
export KAFKA_BROKERS="$BROKERS"
./run_stress_test.sh

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Remote Test Complete!${NC}"
echo -e "${GREEN}========================================${NC}\n"
