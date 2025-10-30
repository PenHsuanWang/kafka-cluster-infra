# Kafka Cluster Stress Test Suite

Comprehensive stress testing framework for Kafka cluster with multiple producers and consumer groups, including detailed timing analysis and visualization.

## Features

- ✅ **Multi-Producer Testing**: 10 concurrent producers sending 100,000 total messages
- ✅ **Multi-Consumer Testing**: 15 consumers across 5 consumer groups
- ✅ **Real-World Simulation**: Mimics actual production workloads
- ✅ **Performance Metrics**: Throughput, latency (P50, P95, P99), success rates
- ✅ **End-to-End Latency**: Measures complete message pipeline
- ✅ **Detailed Timing Analysis**: Tracks t1→t2 (Producer→Kafka) and t2→t3 (Kafka→Consumer)
- ✅ **Comprehensive Visualizations**: matplotlib charts for timing analysis
- ✅ **Comprehensive Reports**: Detailed markdown reports with assessments

## Quick Start

```bash
cd stress-test
./run_stress_test.sh
```

This will:
1. Setup Python environment
2. Create test topic
3. Run producer stress test (100K messages)
4. Run consumer stress test
5. Generate comprehensive report

## Configuration

Edit `config.py` to adjust:

```python
NUM_PRODUCERS = 10               # Number of concurrent producers
MESSAGES_PER_PRODUCER = 10000    # Messages per producer
MESSAGE_SIZE_BYTES = 1024        # Message size (1KB)
NUM_CONSUMER_GROUPS = 5          # Number of consumer groups
CONSUMERS_PER_GROUP = 3          # Consumers per group
```

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

## Troubleshooting

**Connection errors**: Ensure Kafka cluster is running
```bash
docker-compose ps
```

**Slow performance**: Check broker resources
```bash
docker stats kafka-1 kafka-2 kafka-3
```

**Import errors**: Install dependencies
```bash
pip install -r requirements.txt
```
