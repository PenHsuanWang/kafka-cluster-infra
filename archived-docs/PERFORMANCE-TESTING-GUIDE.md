# Kafka Cluster Performance Testing Guide

> **Target Audience:** QA Engineers, Performance Testers, System Analysts  
> **Last Updated:** 2025-10-30  
> **Version:** 1.0

## Table of Contents
1. [Overview](#overview)
2. [Test Environment Setup](#test-environment-setup)
3. [Performance Test Types](#performance-test-types)
4. [Test Execution](#test-execution)
5. [Metrics Collection](#metrics-collection)
6. [Performance Baselines](#performance-baselines)
7. [Troubleshooting](#troubleshooting)

---

## Overview

This guide provides comprehensive instructions for performance testing the Kafka cluster from a QA and systems analysis perspective.

### Performance Testing Objectives

1. **Baseline Establishment:** Determine baseline throughput and latency
2. **Capacity Planning:** Identify maximum sustainable load
3. **Bottleneck Identification:** Find system constraints
4. **SLA Validation:** Verify performance SLAs are met
5. **Regression Prevention:** Ensure changes don't degrade performance

### Key Performance Indicators (KPIs)

| Metric | Target | Critical Threshold | Unit |
|--------|--------|-------------------|------|
| Producer Throughput | ≥ 100 MB/s | < 50 MB/s | MB/sec |
| Producer Latency (P99) | ≤ 100 ms | > 500 ms | milliseconds |
| Consumer Throughput | ≥ 150 MB/s | < 75 MB/s | MB/sec |
| Consumer Lag | ≤ 1000 msgs | > 10000 msgs | messages |
| Under-Replicated Partitions | 0 | > 0 | count |
| CPU Usage (per broker) | ≤ 70% | > 85% | percent |
| Memory Usage (per broker) | ≤ 80% | > 90% | percent |
| Disk Usage | ≤ 80% | > 90% | percent |
| Request Latency (P99) | ≤ 100 ms | > 500 ms | milliseconds |

---

## Test Environment Setup

### Prerequisites

1. **Hardware Requirements:**
   ```bash
   # Minimum for testing
   - CPU: 8 cores (16 threads)
   - RAM: 24 GB
   - Disk: 100 GB SSD/NVMe
   - Network: 1 Gbps
   
   # Recommended for production simulation
   - CPU: 16 cores (32 threads)
   - RAM: 48 GB
   - Disk: 500 GB NVMe
   - Network: 10 Gbps
   ```

2. **Software Requirements:**
   ```bash
   # Check versions
   docker --version          # ≥ 20.10
   docker-compose --version  # ≥ 2.0
   python --version          # ≥ 3.8 (for stress tests)
   ```

3. **Verify Cluster Health:**
   ```bash
   make health
   # All services should show "Up (healthy)"
   ```

### Environment Variables

Create `.env` file with test configurations:

```bash
# Performance Test Configuration
KAFKA_HEAP_SIZE=8G
TEST_DURATION=300                # 5 minutes
TEST_MESSAGE_SIZE=102400         # 100KB
TEST_THROUGHPUT_TARGET=1000      # msgs/sec
TEST_NUM_PARTITIONS=12
TEST_REPLICATION_FACTOR=3
```

---

## Performance Test Types

### 1. Baseline Performance Test

**Objective:** Establish baseline metrics under normal load

**Configuration:**
```bash
# Run baseline test
./scripts/performance-test.sh

# Or using make
make test
```

**Expected Results:**
- Producer: 2,000-5,000 msgs/sec
- Consumer: 10,000-20,000 msgs/sec
- Latency P99: < 100ms

### 2. Load Test

**Objective:** Test behavior under expected production load

```bash
# Producer load test
docker exec kafka-1 kafka-producer-perf-test \
  --topic load-test-topic \
  --num-records 100000 \
  --record-size 102400 \
  --throughput 1000 \
  --producer-props \
    bootstrap.servers=kafka-1:19092,kafka-2:19093,kafka-3:19094 \
    acks=all \
    compression.type=lz4 \
    linger.ms=100 \
    batch.size=1048576 \
    buffer.memory=67108864

# Consumer load test
docker exec kafka-1 kafka-consumer-perf-test \
  --topic load-test-topic \
  --bootstrap-server kafka-1:19092 \
  --messages 100000 \
  --threads 12 \
  --group load-test-consumer \
  --show-detailed-stats
```

**Validation Criteria:**
- [ ] Throughput meets target (100 MB/s)
- [ ] Latency P99 < 100ms
- [ ] No under-replicated partitions
- [ ] CPU < 70%
- [ ] Memory < 80%

### 3. Stress Test

**Objective:** Determine maximum capacity and breaking point

```bash
# Run comprehensive stress test
cd stress-test
./run_stress_test.sh

# Or individual tests
python3 producer_stress.py
python3 consumer_stress.py
python3 report_generator.py
```

**Test Parameters:**
- Concurrent producers: 10
- Concurrent consumer groups: 5
- Message volume: 100,000+
- Duration: 5-10 minutes

**What to Monitor:**
- CPU spikes
- Memory consumption
- GC pauses
- Under-replicated partitions
- Network saturation

### 4. Endurance Test (Soak Test)

**Objective:** Verify stability over extended period

```bash
# Create endurance test script
cat > endurance-test.sh << 'EOF'
#!/bin/bash
DURATION=14400  # 4 hours
END=$((SECONDS+DURATION))

while [ $SECONDS -lt $END ]; do
    docker exec kafka-1 kafka-producer-perf-test \
      --topic endurance-test \
      --num-records 10000 \
      --record-size 10240 \
      --throughput 500 \
      --producer-props bootstrap.servers=kafka-1:19092 acks=all
    sleep 60
done
EOF

chmod +x endurance-test.sh
./endurance-test.sh
```

**Monitoring Focus:**
- Memory leaks
- GC frequency increase
- Log segment growth
- Disk I/O patterns
- Network stability

### 5. Spike Test

**Objective:** Test behavior under sudden load increase

```bash
# Normal load for 2 minutes
for i in {1..120}; do
  docker exec -d kafka-1 kafka-producer-perf-test \
    --topic spike-test \
    --num-records 100 \
    --record-size 1024 \
    --throughput 100 \
    --producer-props bootstrap.servers=kafka-1:19092
  sleep 1
done

# Sudden spike for 30 seconds
for i in {1..30}; do
  for j in {1..10}; do
    docker exec -d kafka-1 kafka-producer-perf-test \
      --topic spike-test \
      --num-records 1000 \
      --record-size 10240 \
      --throughput -1 \
      --producer-props bootstrap.servers=kafka-1:19092
  done
  sleep 1
done

# Back to normal
for i in {1..120}; do
  docker exec -d kafka-1 kafka-producer-perf-test \
    --topic spike-test \
    --num-records 100 \
    --record-size 1024 \
    --throughput 100 \
    --producer-props bootstrap.servers=kafka-1:19092
  sleep 1
done
```

**Validation:**
- [ ] System recovers without intervention
- [ ] No message loss during spike
- [ ] Latency returns to baseline
- [ ] No persistent under-replicated partitions

### 6. Failover Test

**Objective:** Test high availability and fault tolerance

```bash
# Step 1: Start continuous load
docker exec -d kafka-1 kafka-producer-perf-test \
  --topic failover-test \
  --num-records 1000000 \
  --record-size 10240 \
  --throughput 500 \
  --producer-props bootstrap.servers=kafka-1:19092,kafka-2:19093,kafka-3:19094 acks=all

# Step 2: Kill one broker
docker-compose stop kafka-1

# Step 3: Monitor (should continue working)
watch -n 1 'docker exec kafka-2 kafka-topics --describe \
  --bootstrap-server kafka-2:19093 --topic failover-test \
  | grep "Isr:"'

# Step 4: Restart broker after 2 minutes
sleep 120
docker-compose start kafka-1

# Step 5: Verify recovery
make health
```

**Validation:**
- [ ] No message loss
- [ ] Service continues with 2 brokers
- [ ] ISR recovers automatically
- [ ] Partitions rebalance correctly

### 7. Network Latency Test

**Objective:** Simulate network degradation

```bash
# Install tc (traffic control) if not available
docker exec kafka-1 apt-get update && apt-get install -y iproute2

# Add latency to broker 1
docker exec kafka-1 tc qdisc add dev eth0 root netem delay 50ms

# Run producer test
docker exec kafka-1 kafka-producer-perf-test \
  --topic latency-test \
  --num-records 10000 \
  --record-size 10240 \
  --throughput 500 \
  --producer-props bootstrap.servers=kafka-1:19092

# Remove latency
docker exec kafka-1 tc qdisc del dev eth0 root netem
```

---

## Test Execution

### Pre-Test Checklist

- [ ] Cluster health verified (`make health`)
- [ ] No under-replicated partitions
- [ ] Sufficient disk space (> 50 GB free)
- [ ] Monitoring systems operational
- [ ] Test topics created with correct configuration
- [ ] Baseline metrics documented

### Execution Steps

1. **Prepare Environment:**
   ```bash
   # Clear previous test data
   docker exec kafka-1 kafka-topics --delete --topic 'test-.*' \
     --bootstrap-server kafka-1:19092 || true
   
   # Create fresh test topics
   ./scripts/create-topics.sh
   ```

2. **Start Monitoring:**
   ```bash
   # Terminal 1: Resource monitoring
   watch -n 1 'docker stats --no-stream kafka-1 kafka-2 kafka-3'
   
   # Terminal 2: Cluster metrics
   watch -n 5 './scripts/health-check.sh'
   
   # Terminal 3: Kafka UI
   open http://localhost:8080
   ```

3. **Execute Test:**
   ```bash
   # Run selected test type
   ./scripts/performance-test.sh
   # OR
   cd stress-test && ./run_stress_test.sh
   ```

4. **Collect Results:**
   ```bash
   # Save metrics
   docker stats --no-stream > test-results/resource-usage.txt
   docker-compose logs > test-results/cluster-logs.txt
   
   # Export JMX metrics
   docker exec kafka-1 kafka-run-class kafka.tools.JmxTool \
     --object-name kafka.server:type=BrokerTopicMetrics,name=* \
     --jmx-url service:jmx:rmi:///jndi/rmi://localhost:9999/jmxrmi \
     --reporting-interval 1000 \
     --date-format yyyy-MM-dd_HH:mm:ss > test-results/jmx-metrics.txt
   ```

### Post-Test Checklist

- [ ] Test results documented
- [ ] Metrics exported and saved
- [ ] Issues identified and logged
- [ ] Cluster health restored
- [ ] Test topics cleaned up (optional)
- [ ] Results compared with baseline

---

## Metrics Collection

### Real-Time Monitoring

#### 1. Resource Metrics (Docker Stats)

```bash
# Continuous monitoring
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Export to CSV
docker stats --no-stream --format "{{.Container}},{{.CPUPerc}},{{.MemUsage}}" > metrics.csv
```

#### 2. JMX Metrics

```bash
# Broker topic metrics
docker exec kafka-1 kafka-run-class kafka.tools.JmxTool \
  --object-name kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec \
  --jmx-url service:jmx:rmi:///jndi/rmi://localhost:9999/jmxrmi \
  --reporting-interval 5000

# Request metrics
docker exec kafka-1 kafka-run-class kafka.tools.JmxTool \
  --object-name kafka.network:type=RequestMetrics,name=TotalTimeMs,request=Produce \
  --jmx-url service:jmx:rmi:///jndi/rmi://localhost:9999/jmxrmi \
  --reporting-interval 5000

# Replica manager metrics
docker exec kafka-1 kafka-run-class kafka.tools.JmxTool \
  --object-name kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions \
  --jmx-url service:jmx:rmi:///jndi/rmi://localhost:9999/jmxrmi \
  --reporting-interval 5000
```

#### 3. Topic-Level Metrics

```bash
# Describe topic
docker exec kafka-1 kafka-topics --describe \
  --bootstrap-server kafka-1:19092 \
  --topic test-topic

# Get consumer group lag
docker exec kafka-1 kafka-consumer-groups --describe \
  --bootstrap-server kafka-1:19092 \
  --group test-consumer-group
```

### Automated Metrics Collection

Create monitoring script:

```bash
cat > collect-metrics.sh << 'EOF'
#!/bin/bash
INTERVAL=5
DURATION=300
OUTPUT_DIR="test-results/$(date +%Y%m%d_%H%M%S)"

mkdir -p "$OUTPUT_DIR"

echo "Collecting metrics for ${DURATION} seconds..."

# Docker stats
docker stats --no-stream --format "{{.Container}},{{.CPUPerc}},{{.MemUsage}},{{.NetIO}},{{.BlockIO}}" > "$OUTPUT_DIR/docker-stats.csv" &
DOCKER_PID=$!

# JMX metrics
docker exec kafka-1 kafka-run-class kafka.tools.JmxTool \
  --object-name kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec \
  --jmx-url service:jmx:rmi:///jndi/rmi://localhost:9999/jmxrmi \
  --reporting-interval $((INTERVAL * 1000)) \
  --date-format yyyy-MM-dd_HH:mm:ss > "$OUTPUT_DIR/messages-per-sec.csv" &
JMX_PID=$!

# Wait for duration
sleep $DURATION

# Stop collection
kill $DOCKER_PID $JMX_PID 2>/dev/null

echo "Metrics saved to $OUTPUT_DIR"
EOF

chmod +x collect-metrics.sh
```

---

## Performance Baselines

### Cluster Specifications

```yaml
Cluster Configuration:
  Brokers: 3
  ZooKeeper Nodes: 3
  Replication Factor: 3
  Min ISR: 2
  
Broker Resources (each):
  JVM Heap: 8 GB
  CPU Cores: 8 (allocated)
  Memory: 16 GB
  Disk: NVMe SSD
  Network: 1 Gbps

Topic Configuration:
  Partitions: 12
  Replication: 3
  Compression: LZ4
  Retention: 7 days
```

### Baseline Performance Metrics

#### Producer Performance

| Message Size | Throughput (msgs/sec) | Throughput (MB/sec) | Latency P50 | Latency P99 |
|--------------|----------------------|---------------------|-------------|-------------|
| 1 KB | 5,000 - 8,000 | 5 - 8 | < 5 ms | < 50 ms |
| 10 KB | 2,000 - 4,000 | 20 - 40 | < 10 ms | < 100 ms |
| 100 KB | 1,000 - 2,000 | 100 - 200 | < 20 ms | < 200 ms |
| 1 MB | 100 - 500 | 100 - 500 | < 100 ms | < 500 ms |

#### Consumer Performance

| Message Size | Throughput (msgs/sec) | Throughput (MB/sec) | End-to-End Latency |
|--------------|----------------------|---------------------|-------------------|
| 1 KB | 20,000 - 40,000 | 20 - 40 | < 100 ms |
| 10 KB | 10,000 - 20,000 | 100 - 200 | < 200 ms |
| 100 KB | 2,000 - 5,000 | 200 - 500 | < 500 ms |
| 1 MB | 500 - 1,000 | 500 - 1000 | < 1 sec |

#### Resource Utilization (Normal Load)

| Component | CPU Usage | Memory Usage | Disk I/O | Network I/O |
|-----------|-----------|--------------|----------|-------------|
| Kafka Broker | 15-30% | 2-4 GB | 50-200 MB/s | 100-500 Mbps |
| ZooKeeper | 1-5% | 100-200 MB | < 10 MB/s | < 10 Mbps |
| Overall System | 20-40% | 8-12 GB | 150-600 MB/s | 300-1500 Mbps |

---

## Troubleshooting

### Common Performance Issues

#### 1. Low Producer Throughput

**Symptoms:**
- Throughput < 50 MB/s
- High producer latency (P99 > 500ms)

**Diagnosis:**
```bash
# Check producer configuration
docker exec kafka-1 kafka-configs --describe \
  --entity-type topics --entity-name test-topic \
  --bootstrap-server kafka-1:19092

# Check broker CPU
docker stats kafka-1 kafka-2 kafka-3 --no-stream

# Check network throttling
docker exec kafka-1 kafka-run-class kafka.tools.JmxTool \
  --object-name kafka.server:type=BrokerTopicMetrics,name=BytesRejectedPerSec \
  --jmx-url service:jmx:rmi:///jndi/rmi://localhost:9999/jmxrmi
```

**Solutions:**
- Increase `batch.size` and `linger.ms`
- Use async producers for non-critical data
- Increase `buffer.memory`
- Check network bandwidth
- Verify disk I/O performance

#### 2. High Consumer Lag

**Symptoms:**
- Consumer lag > 10,000 messages
- Lag increasing over time

**Diagnosis:**
```bash
# Check consumer group lag
docker exec kafka-1 kafka-consumer-groups --describe \
  --bootstrap-server kafka-1:19092 \
  --group your-consumer-group

# Check partition distribution
docker exec kafka-1 kafka-topics --describe \
  --bootstrap-server kafka-1:19092 \
  --topic your-topic
```

**Solutions:**
- Add more consumers to group
- Increase partitions
- Optimize consumer processing logic
- Increase `fetch.min.bytes` for batching
- Check for slow consumers

#### 3. Under-Replicated Partitions

**Symptoms:**
- ISR < Replicas
- Data at risk

**Diagnosis:**
```bash
# Find under-replicated partitions
docker exec kafka-1 kafka-topics --describe \
  --bootstrap-server kafka-1:19092 \
  --under-replicated-partitions

# Check broker logs
docker-compose logs kafka-1 | grep -i "under-replicated"

# Check replica fetcher metrics
docker exec kafka-1 kafka-run-class kafka.tools.JmxTool \
  --object-name kafka.server:type=ReplicaFetcherManager,* \
  --jmx-url service:jmx:rmi:///jndi/rmi://localhost:9999/jmxrmi
```

**Solutions:**
- Check broker health
- Verify network connectivity
- Increase `replica.fetch.max.bytes`
- Check disk space
- Restart slow broker

#### 4. High Memory Usage / GC Pauses

**Symptoms:**
- JVM heap usage > 85%
- Long GC pauses (> 1 second)

**Diagnosis:**
```bash
# Check JVM metrics
docker exec kafka-1 kafka-run-class kafka.tools.JmxTool \
  --object-name java.lang:type=Memory \
  --jmx-url service:jmx:rmi:///jndi/rmi://localhost:9999/jmxrmi

# Check GC metrics
docker exec kafka-1 kafka-run-class kafka.tools.JmxTool \
  --object-name java.lang:type=GarbageCollector,name=* \
  --jmx-url service:jmx:rmi:///jndi/rmi://localhost:9999/jmxrmi
```

**Solutions:**
- Increase JVM heap size
- Tune G1GC parameters
- Reduce message retention
- Implement log compaction
- Archive old segments

### Performance Test Validation Matrix

| Test Type | Success Criteria | Warning Threshold | Failure Threshold |
|-----------|-----------------|-------------------|-------------------|
| Baseline | Meets baseline targets | 80% of baseline | < 60% of baseline |
| Load | Sustains target load | Occasional spikes | Consistent degradation |
| Stress | Handles max load | CPU > 80% | System crashes |
| Endurance | Stable for 4+ hours | Memory growth | Memory leaks |
| Spike | Recovers in < 2 min | Recovers in < 5 min | Doesn't recover |
| Failover | < 1 min recovery | < 2 min recovery | > 5 min recovery |

---

## Next Steps

1. Review [MONITORING.md](MONITORING.md) for continuous monitoring setup
2. See [STRESS_TEST_SUMMARY.md](STRESS_TEST_SUMMARY.md) for latest test results
3. Check [JMX-ACCESS-GUIDE.md](JMX-ACCESS-GUIDE.md) for JMX monitoring
4. Refer to [PRODUCTION-CHECKLIST.md](PRODUCTION-CHECKLIST.md) before production deployment

---

**Document Version:** 1.0  
**Last Review:** 2025-10-30  
**Next Review:** After production deployment or quarterly
