# Kafka Cluster Stress Test Suite

Comprehensive stress testing framework for Kafka cluster with multiple producers and consumer groups, including detailed timing analysis and visualization.

**✨ NEW: Remote Cluster Testing** - Now supports testing remote Kafka clusters deployed on VMs or cloud infrastructure!

## Features

- ✅ **Multi-Producer Testing**: 10 concurrent producers sending 100,000 total messages
- ✅ **Multi-Consumer Testing**: 15 consumers across 5 consumer groups
- ✅ **Remote Cluster Support**: Test local or remote Kafka deployments
- ✅ **Real-World Simulation**: Mimics actual production workloads
- ✅ **Performance Metrics**: Throughput, latency (P50, P95, P99), success rates
- ✅ **End-to-End Latency**: Measures complete message pipeline
- ✅ **Detailed Timing Analysis**: Tracks t1→t2 (Producer→Kafka) and t2→t3 (Kafka→Consumer)
- ✅ **Comprehensive Visualizations**: matplotlib charts for timing analysis
- ✅ **Comprehensive Reports**: Detailed markdown reports with assessments

## Quick Start

### Local Testing (Default)
```bash
cd stress-test
./run_stress_test.sh
```

### Remote Testing (NEW!)
```bash
cd stress-test

# Simple: Using helper script
./test-remote.sh vm1:9092 vm2:9092 vm3:9092

# Advanced: Using environment variables
export KAFKA_BROKERS="vm1.example.com:9092,vm2.example.com:9092,vm3.example.com:9092"
./run_stress_test.sh
```

📖 **See [REMOTE-TESTING-GUIDE.md](REMOTE-TESTING-GUIDE.md) for complete remote testing documentation**

This will:
1. Setup Python environment
2. Create test topic
3. Run producer stress test (100K messages)
4. Run consumer stress test
5. Generate comprehensive report

## Configuration

### Via Environment Variables (Recommended)

```bash
# Copy example configuration
cp .env.example .env

# Edit .env file or export variables
export KAFKA_BROKERS="vm1:9092,vm2:9092,vm3:9092"
export NUM_PRODUCERS=20
export MESSAGES_PER_PRODUCER=10000
export MESSAGE_SIZE_BYTES=1024
export NUM_CONSUMER_GROUPS=5
export CONSUMERS_PER_GROUP=3
```

### Via config.py (Legacy)

Edit `config.py` to adjust:

```python
NUM_PRODUCERS = 10               # Number of concurrent producers
MESSAGES_PER_PRODUCER = 10000    # Messages per producer
MESSAGE_SIZE_BYTES = 1024        # Message size (1KB)
NUM_CONSUMER_GROUPS = 5          # Number of consumer groups
CONSUMERS_PER_GROUP = 3          # Consumers per group
```

All settings support environment variable override.

## Individual Tests

Run tests separately:

```bash
# Producer test only
python3 producer_stress.py

# Consumer test only
python3 consumer_stress.py

# Generate report and visualizations
python3 report_generator.py

# Generate visualizations only
python3 visualization.py
```

## Timing Analysis

The stress test tracks three key timestamps:
- **t1**: Message send time (when producer calls `produce()`)
- **t2**: Kafka acknowledgment time (when broker confirms write)
- **t3**: Consumer receive time (when consumer polls the message)

Measured intervals:
- **t2 - t1**: Producer→Kafka latency (network + broker processing)
- **t3 - t2**: Kafka→Consumer latency (storage + consumer poll)
- **t3 - t1**: End-to-end latency (complete pipeline)

## Results

Test results are saved in `test-results/`:
- `STRESS_TEST_REPORT.md` - Main performance report
- `producer_results.json` - Detailed producer metrics
- `consumer_results.json` - Detailed consumer metrics
- `producer_timing_data.json` - Detailed timing data for Producer→Kafka
- `consumer_timing_data.json` - Detailed timing data for Kafka→Consumer

### Visualization Charts

Automatically generated charts:
- `timing_breakdown.png` - Average latency breakdown (t2-t1 and t3-t2)
- `timing_vs_throughput.png` - Latency variation vs message throughput
- `end_to_end_pipeline.png` - Complete pipeline timing visualization
- `latency_distribution.png` - Latency distribution histograms
- `throughput_comparison.png` - Producer vs Consumer throughput

## Performance Thresholds

Default SLA targets:
- **Success Rate**: ≥99%
- **Throughput**: ≥5 MB/s
- **P99 Latency**: <100ms

## Test Scenarios

### Producer Test
- 10 concurrent producers
- 10,000 messages each = 100,000 total
- 1KB message size = ~100MB data
- LZ4 compression
- `acks=all` (full replication)

### Consumer Test
- 5 consumer groups (parallel processing)
- 3 consumers per group = 15 total consumers
- Measures end-to-end latency
- Auto-commit enabled

## Cleanup

Remove test topic after testing:

```bash
docker exec kafka-1 kafka-topics --delete \
  --bootstrap-server kafka-1:19092 \
  --topic stress-test-topic
```

## Requirements

- Python 3.7+
- confluent-kafka
- tqdm
- Running Kafka cluster

## Remote Testing Examples

### Example 1: Test Production Cluster
```bash
export KAFKA_BROKERS="prod-kafka1.company.com:9092,prod-kafka2.company.com:9092,prod-kafka3.company.com:9092"
./run_stress_test.sh
```

### Example 2: High Throughput Test
```bash
export KAFKA_BROKERS="10.0.1.10:9092,10.0.1.11:9092,10.0.1.12:9092"
export NUM_PRODUCERS=20
export MESSAGES_PER_PRODUCER=50000
export MESSAGE_SIZE_BYTES=10240  # 10KB
./run_stress_test.sh
```

### Example 3: Quick Smoke Test
```bash
./test-remote.sh kafka1.local:9092 kafka2.local:9092 kafka3.local:9092
```

## Troubleshooting

**Connection errors**: Ensure Kafka cluster is running
```bash
# Local
docker-compose ps

# Remote - test connectivity
nc -zv vm1.example.com 9092
```

**Slow performance**: Check broker resources
```bash
# Local
docker stats kafka-1 kafka-2 kafka-3

# Remote - monitor via SSH
ssh vm1 "docker stats kafka-1"
```

**Import errors**: Install dependencies
```bash
pip install -r requirements.txt
```

**Remote connectivity issues**: See [REMOTE-TESTING-GUIDE.md](REMOTE-TESTING-GUIDE.md) for detailed troubleshooting
