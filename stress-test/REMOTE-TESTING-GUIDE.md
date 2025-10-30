# Remote Kafka Cluster Testing Guide

This guide explains how to run stress tests against a remote Kafka cluster deployed on VMs or cloud infrastructure.

## Quick Start

### Local Testing (Default)
```bash
cd stress-test
./run_stress_test.sh
```

### Remote Testing
```bash
export KAFKA_BROKERS="vm1.example.com:9092,vm2.example.com:9092,vm3.example.com:9092"
cd stress-test
./run_stress_test.sh
```

---

## Configuration

### Environment Variables

All test parameters can be configured via environment variables:

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `KAFKA_BROKERS` | Comma-separated list of broker addresses | `localhost:9092,localhost:9093,localhost:9094` | `vm1:9092,vm2:9092,vm3:9092` |
| `TEST_TOPIC` | Topic name for testing | `stress-test-topic` | `perf-test-topic` |
| `NUM_PRODUCERS` | Number of concurrent producers | `10` | `20` |
| `MESSAGES_PER_PRODUCER` | Messages per producer | `10000` | `50000` |
| `MESSAGE_SIZE_BYTES` | Size of each message | `1024` (1KB) | `10240` (10KB) |
| `NUM_CONSUMER_GROUPS` | Number of consumer groups | `5` | `10` |
| `CONSUMERS_PER_GROUP` | Consumers per group | `3` | `5` |
| `TEST_DURATION_SECONDS` | Max test duration | `300` | `600` |
| `TOPIC_PARTITIONS` | Number of partitions | `12` | `24` |
| `TOPIC_REPLICATION_FACTOR` | Replication factor | `3` | `3` |
| `TOPIC_MIN_ISR` | Minimum in-sync replicas | `2` | `2` |

---

## Testing Scenarios

### 1. Basic Remote Test

Test a remote 3-node cluster:

```bash
export KAFKA_BROKERS="10.0.1.10:9092,10.0.1.11:9092,10.0.1.12:9092"
cd stress-test
./run_stress_test.sh
```

### 2. High Throughput Test

Test with larger messages and more producers:

```bash
export KAFKA_BROKERS="prod-kafka-1:9092,prod-kafka-2:9092,prod-kafka-3:9092"
export NUM_PRODUCERS=20
export MESSAGES_PER_PRODUCER=50000
export MESSAGE_SIZE_BYTES=10240  # 10KB
cd stress-test
./run_stress_test.sh
```

### 3. Multi-Region Test

Test cluster with hostnames/FQDNs:

```bash
export KAFKA_BROKERS="kafka1.us-east.company.com:9092,kafka2.us-east.company.com:9092,kafka3.us-east.company.com:9092"
export TEST_TOPIC="multi-region-test"
cd stress-test
./run_stress_test.sh
```

### 4. Custom Configuration Test

Full custom configuration:

```bash
export KAFKA_BROKERS="192.168.1.101:9092,192.168.1.102:9092,192.168.1.103:9092"
export TEST_TOPIC="custom-perf-test"
export NUM_PRODUCERS=15
export MESSAGES_PER_PRODUCER=20000
export MESSAGE_SIZE_BYTES=2048
export NUM_CONSUMER_GROUPS=8
export CONSUMERS_PER_GROUP=4
export TOPIC_PARTITIONS=24
cd stress-test
./run_stress_test.sh
```

---

## Pre-requisites for Remote Testing

### 1. Network Connectivity

Ensure your test machine can reach the Kafka brokers:

```bash
# Test connectivity to each broker
nc -zv 10.0.1.10 9092
nc -zv 10.0.1.11 9092
nc -zv 10.0.1.12 9092

# Or use telnet
telnet 10.0.1.10 9092
```

### 2. Firewall Rules

Ensure the following ports are open:
- **9092, 9093, 9094**: Kafka broker ports (or your custom ports)
- **2181**: ZooKeeper (if needed for admin operations)

### 3. DNS/Hostname Resolution

If using hostnames, ensure they resolve correctly:

```bash
# Test hostname resolution
ping kafka1.example.com
nslookup kafka1.example.com

# Or add to /etc/hosts if needed
echo "10.0.1.10 kafka1.example.com" | sudo tee -a /etc/hosts
```

### 4. Authentication (if enabled)

If your cluster uses SASL/SSL authentication, you'll need to configure additional settings. Create a `.env` file:

```bash
# .env file
export KAFKA_BROKERS="secure-kafka1:9093,secure-kafka2:9093,secure-kafka3:9093"
export KAFKA_SECURITY_PROTOCOL="SASL_SSL"
export KAFKA_SASL_MECHANISM="PLAIN"
export KAFKA_SASL_USERNAME="your-username"
export KAFKA_SASL_PASSWORD="your-password"
```

Then modify `config.py` to include security settings.

---

## Testing Workflow

### Step 1: Setup Environment

```bash
cd stress-test

# For remote testing
export KAFKA_BROKERS="vm1:9092,vm2:9092,vm3:9092"

# Optional: Customize test parameters
export NUM_PRODUCERS=20
export MESSAGES_PER_PRODUCER=10000
```

### Step 2: Verify Connectivity

```bash
# Test broker connectivity
python3 -c "
from confluent_kafka.admin import AdminClient
import os
brokers = os.getenv('KAFKA_BROKERS', 'localhost:9092')
admin = AdminClient({'bootstrap.servers': brokers})
metadata = admin.list_topics(timeout=10)
print(f'✓ Connected to {len(metadata.brokers)} brokers')
for broker in metadata.brokers.values():
    print(f'  - Broker {broker.id}: {broker.host}:{broker.port}')
"
```

### Step 3: Run Test

```bash
./run_stress_test.sh
```

### Step 4: Review Results

```bash
# View detailed report
cat test-results/STRESS_TEST_REPORT.md

# View JSON results
cat test-results/producer_results.json
cat test-results/consumer_results.json
```

---

## Individual Test Scripts

### Run Producer Test Only

```bash
export KAFKA_BROKERS="vm1:9092,vm2:9092,vm3:9092"
cd stress-test
source venv/bin/activate
python3 producer_stress.py
```

### Run Consumer Test Only

```bash
export KAFKA_BROKERS="vm1:9092,vm2:9092,vm3:9092"
cd stress-test
source venv/bin/activate
python3 consumer_stress.py
```

### Generate Report from Existing Results

```bash
cd stress-test
source venv/bin/activate
python3 report_generator.py
```

---

## Docker Deployment Scenario

If you've deployed this Kafka cluster using Docker on remote VMs:

### Architecture Example

```
VM1 (10.0.1.10):
  - zookeeper-1
  - kafka-1 (port 9092)

VM2 (10.0.1.11):
  - zookeeper-2
  - kafka-2 (port 9092)

VM3 (10.0.1.12):
  - zookeeper-3
  - kafka-3 (port 9092)
```

### Testing from Local Machine

```bash
# Set broker addresses (external IP:port)
export KAFKA_BROKERS="10.0.1.10:9092,10.0.1.11:9092,10.0.1.12:9092"

# Run test
cd stress-test
./run_stress_test.sh
```

### Testing from Another VM in Same Network

```bash
# Use internal IPs or hostnames
export KAFKA_BROKERS="vm1:9092,vm2:9092,vm3:9092"

# Or use container names if on same Docker network
export KAFKA_BROKERS="kafka-1:19092,kafka-2:19093,kafka-3:19094"

cd stress-test
./run_stress_test.sh
```

---

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to remote brokers

```bash
# Check network connectivity
ping vm1.example.com
nc -zv vm1.example.com 9092

# Verify broker addresses
echo $KAFKA_BROKERS

# Test with kafkacat (if installed)
kafkacat -L -b vm1.example.com:9092
```

### Advertised Listeners Mismatch

**Problem**: Connected but getting errors about broker hostnames

**Solution**: Check that `KAFKA_ADVERTISED_LISTENERS` in docker-compose.yml matches the addresses you're using:

```yaml
# On remote VM docker-compose.yml
KAFKA_ADVERTISED_LISTENERS: INTERNAL://kafka-1:19092,EXTERNAL://10.0.1.10:9092
```

Update your test command:
```bash
export KAFKA_BROKERS="10.0.1.10:9092,10.0.1.11:9092,10.0.1.12:9092"
```

### Topic Already Exists

**Problem**: Topic creation fails because it already exists

**Solution**: Either delete the existing topic or the script will automatically continue:

```bash
# Delete topic (from VM with docker access)
docker exec kafka-1 kafka-topics --delete \
  --bootstrap-server localhost:9092 \
  --topic stress-test-topic

# Or use a different topic name
export TEST_TOPIC="new-perf-test-$(date +%s)"
```

### Timeout Issues

**Problem**: Test times out when waiting for messages

**Solution**: Increase timeout and check consumer lag:

```bash
# Increase consumer timeout
export TEST_DURATION_SECONDS=600

# Check consumer lag (on VM)
docker exec kafka-1 kafka-consumer-groups --bootstrap-server localhost:9092 \
  --describe --group stress-test-group-0
```

---

## Performance Baseline

Expected results for a 3-broker cluster (8GB RAM each):

| Metric | Local (Docker) | Remote (LAN) | Remote (WAN) |
|--------|---------------|--------------|--------------|
| **Producer Throughput** | 80-100 MB/s | 60-80 MB/s | 20-50 MB/s |
| **Consumer Throughput** | 80-100 MB/s | 60-80 MB/s | 20-50 MB/s |
| **P99 Latency** | 20-50 ms | 30-80 ms | 100-300 ms |
| **Success Rate** | 100% | 100% | 99.9%+ |

---

## Best Practices

### 1. Network Optimization

- Use machines in the same datacenter/region for testing
- Ensure adequate network bandwidth (1Gbps+ recommended)
- Monitor network latency: `ping -c 100 kafka-host`

### 2. Test Incrementally

Start with small tests and scale up:

```bash
# Small test
export NUM_PRODUCERS=5
export MESSAGES_PER_PRODUCER=1000

# Medium test
export NUM_PRODUCERS=10
export MESSAGES_PER_PRODUCER=10000

# Large test
export NUM_PRODUCERS=20
export MESSAGES_PER_PRODUCER=50000
```

### 3. Monitor Remote Cluster

While testing, monitor the remote cluster:

```bash
# Check broker metrics
docker stats kafka-1 kafka-2 kafka-3

# Check disk usage
docker exec kafka-1 df -h /var/lib/kafka/data

# Check logs
docker logs -f kafka-1
```

### 4. Clean Up After Testing

```bash
# Delete test topics
docker exec kafka-1 kafka-topics --delete \
  --bootstrap-server localhost:9092 \
  --topic stress-test-topic

# Clear consumer groups
docker exec kafka-1 kafka-consumer-groups --bootstrap-server localhost:9092 \
  --delete --group stress-test-group-0
```

---

## Example: Complete Remote Test

```bash
#!/bin/bash
# complete-remote-test.sh

set -e

echo "=== Remote Kafka Cluster Performance Test ==="

# Configuration
export KAFKA_BROKERS="prod-kafka1.company.com:9092,prod-kafka2.company.com:9092,prod-kafka3.company.com:9092"
export TEST_TOPIC="perf-test-$(date +%Y%m%d-%H%M%S)"
export NUM_PRODUCERS=15
export MESSAGES_PER_PRODUCER=20000
export MESSAGE_SIZE_BYTES=2048
export NUM_CONSUMER_GROUPS=5
export CONSUMERS_PER_GROUP=3

echo "Brokers: $KAFKA_BROKERS"
echo "Topic: $TEST_TOPIC"
echo "Total Messages: $((NUM_PRODUCERS * MESSAGES_PER_PRODUCER))"

# Test connectivity
echo -e "\nTesting connectivity..."
for broker in ${KAFKA_BROKERS//,/ }; do
    host=$(echo $broker | cut -d: -f1)
    port=$(echo $broker | cut -d: -f2)
    if nc -zv -w5 $host $port 2>&1 | grep -q "succeeded"; then
        echo "✓ $broker reachable"
    else
        echo "✗ $broker NOT reachable"
        exit 1
    fi
done

# Run test
echo -e "\nRunning stress test..."
cd stress-test
./run_stress_test.sh

echo -e "\n=== Test Complete ==="
echo "Results: stress-test/test-results/STRESS_TEST_REPORT.md"
```

---

## Support

For issues or questions:
1. Check connectivity with `nc -zv <host> <port>`
2. Verify broker configuration in docker-compose.yml
3. Review logs: `docker logs kafka-1`
4. Check network latency: `ping -c 100 <host>`

---

**Last Updated**: 2025-10-30
