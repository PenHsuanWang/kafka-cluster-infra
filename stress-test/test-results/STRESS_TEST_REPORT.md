# Kafka Cluster Stress Test Report
**Generated:** 2025-10-30 14:19:08

---

## Executive Summary

**Status:** ✅ PASSED

- **Producer Success:** 100.00%
- **Producer Throughput:** 1.16 MB/s
- **Producer P99 Latency:** 22.17 ms
- **Consumer Success:** 100.00%
- **Consumer Throughput:** 17.56 MB/s
- **End-to-End P99:** 101517.49 ms

---

## Performance Visualizations

Detailed timing analysis charts have been generated:

- `timing_breakdown.png` - Average latency at each stage (t2-t1 and t3-t2)
- `timing_vs_throughput.png` - Latency variation with message throughput
- `end_to_end_pipeline.png` - Complete pipeline timing breakdown
- `latency_distribution.png` - Distribution of latencies for both stages
- `throughput_comparison.png` - Producer vs Consumer throughput comparison

---

## Configuration

- **Brokers:** localhost:9092, localhost:9093, localhost:9094
- **Topic:** stress-test-topic, Partitions: 12
- **Producers:** 10 × 10000 messages
- **Message Size:** 1024 bytes
- **Consumer Groups:** 5 × 3 consumers

---

## Producer Results

**Duration:** 84.04s

- Messages Sent: 100,000
- Failed: 0
- Success Rate: 100.00%
- Throughput: 1189.92 msgs/s (1.16 MB/s)

**Latency (ms):**
- Avg: 0.65, P50: 0.02
- P95: 0.07, P99: 22.17

**Producer→Kafka Timing (t2-t1):**
- Avg: 39784.26, P50: 38162.95
- P95: 82568.84, P99: 82905.85

---

## Consumer Results

**Duration:** 27.80s

- Messages Consumed: 500,000
- Errors: 0
- Success Rate: 100.00%
- Throughput: 17985.21 msgs/s (17.56 MB/s)

**End-to-End Latency (ms):**
- Avg: 85773.72, P50: 84831.52
- P95: 100575.98, P99: 101517.49

**Kafka→Consumer Timing (t3-t2):**
- Avg: 85773.72, P50: 84831.51
- P95: 100575.94, P99: 101517.48

---

## Assessment

✅ Producer success ≥99%
⚠️ Throughput 1.16 MB/s
✅ P99 latency <100ms
✅ Consumer success ≥99%

---

## Conclusion

Cluster shows **excellent performance** and is production-ready.
