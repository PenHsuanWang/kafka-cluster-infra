# Production-Ready Kafka Cluster

> **Version:** 2.0 | **Last Updated:** 2025-10-30

A production-ready Apache Kafka cluster with comprehensive documentation for users and developers.

## 📚 Documentation

This project has **two main guides**:

### 1. [USER-GUIDE.md](USER-GUIDE.md) - For Operations & QA
**For:** System Administrators, DevOps Engineers, QA Engineers

Complete guide covering:
- ✅ Getting Started (3-step quick start)
- ✅ Cluster Management (start/stop, topics, consumer groups)
- ✅ Monitoring & Observability (Kafka UI, JMX, health checks)
- ✅ Performance Testing (baselines, stress tests)
- ✅ Production Deployment (checklist, configuration)
- ✅ Troubleshooting (common issues, solutions)

### 2. [DEVELOPER-GUIDE-COMPLETE.md](DEVELOPER-GUIDE-COMPLETE.md) - For Developers
**For:** Software Engineers, Application Developers

Complete guide covering:
- ✅ Connection Configuration (bootstrap servers, serializers)
- ✅ Producer Development (4 patterns with code examples)
- ✅ Consumer Development (4 patterns with code examples)
- ✅ Best Practices (topic design, error handling, testing)
- ✅ Code Examples (Java, Python, Node.js, Go)
- ✅ Troubleshooting (connection, latency, duplicates)

---

## Architecture

- **3 ZooKeeper nodes** - Ensemble mode for coordination
- **3 Kafka brokers** - Replication factor 3, min ISR 2
- **Rack-aware placement** - Fault tolerance across failure domains
- **Kafka UI** - Web-based monitoring at http://localhost:8080
- **JMX monitoring** - Metrics on ports 9999, 10000, 10001
- **Target throughput:** ~100 MB/s (1,000 msgs/sec @ 100KB)

## Prerequisites

**System:**
- Docker 20.10+ and Docker Compose 2.0+
- 24GB RAM minimum (8GB per broker)
- 100GB disk minimum (SSD/NVMe recommended)

**Verify installation:**
```bash
docker --version
docker-compose --version
```

## 🚀 Quick Start (3 Steps)

### 1. Start Cluster

```bash
# Using start script (recommended - includes health checks)
./scripts/start-cluster.sh

# Or using make
make start
```

The cluster will start:
- 3 ZooKeeper nodes
- 3 Kafka brokers
- Kafka UI web console
- JMX exporters for monitoring

### 2. Verify Health

```bash
make health
```

Expected output:
```
✓ ZooKeeper-1: OK
✓ ZooKeeper-2: OK
✓ ZooKeeper-3: OK
✓ Kafka-1: OK
✓ Kafka-2: OK
✓ Kafka-3: OK
✓ No under-replicated partitions
```

### 3. Access Kafka UI

Open http://localhost:8080 to see:
- Cluster health dashboard
- Topic management
- Consumer group monitoring
- Real-time metrics

---

## 📖 What's Next?

### For Users/Operators
👉 **See [USER-GUIDE.md](USER-GUIDE.md)** for:
- Cluster management operations
- Topic and consumer group management
- Monitoring and health checks
- Performance testing procedures
- Production deployment checklist
- Complete troubleshooting guide

### For Developers
👉 **See [DEVELOPER-GUIDE-COMPLETE.md](DEVELOPER-GUIDE-COMPLETE.md)** for:
- Producer/Consumer code examples (Java, Python, Node.js, Go)
- 4 producer patterns (Fire-and-forget, Async, Sync, Transactional)
- 4 consumer patterns (Auto-commit, Manual, Batch, Multi-threaded)
- Best practices and testing strategies
- Configuration recommendations
- Integration troubleshooting

---

## Quick Reference

### Access Points
| Service | URL/Endpoint | Purpose |
|---------|--------------|---------|
| **Kafka UI** | http://localhost:8080 | Web console (primary) |
| **Kafka Brokers** | localhost:9092, 9093, 9094 | Client connections |
| **JMX Metrics** | localhost:9999, 10000, 10001 | JConsole/VisualVM |

### Essential Commands
```bash
make start          # Start cluster
make stop           # Stop cluster
make health         # Health check
make test           # Quick performance test
make logs           # View logs
make ui             # Open Kafka UI

# Stress test (comprehensive)
cd stress-test && ./run_stress_test.sh
```

### Test Results
- ✅ **100% success rate** - Zero message loss in all tests
- ✅ **100,000+ messages** tested with 10 concurrent producers
- ✅ **5 consumer groups** validated (15 consumers total)
- ✅ **Perfect reliability** - All replicas in-sync

**Run Your Own Stress Test:**
```bash
cd stress-test
./run_stress_test.sh
```

See [STRESS-TEST-GUIDE.md](STRESS-TEST-GUIDE.md) for step-by-step instructions and expected outcomes.

---

## Project Structure

```
kafka-cluster-infra/
├── README.md                         # This file (overview)
├── USER-GUIDE.md                     # ⭐ Complete user/ops guide
├── DEVELOPER-GUIDE-COMPLETE.md       # ⭐ Complete developer guide
├── STRESS_TEST_SUMMARY.md            # Test results & analysis
├── TEST_RESULTS.md                   # Initial validation results
├── docker-compose.yml                # Cluster configuration
├── Makefile                          # Automation commands
├── .env                              # Environment variables
├── config/                           # Configuration files
│   ├── jmx-exporter-config.yml
│   └── prometheus/                   # (Optional) Prometheus setup
├── scripts/                          # Helper scripts
│   ├── start-cluster.sh
│   ├── stop-cluster.sh
│   ├── health-check.sh
│   ├── create-topics.sh
│   └── performance-test.sh
├── stress-test/                      # Stress testing suite
│   ├── producer_stress.py
│   ├── consumer_stress.py
│   └── run_stress_test.sh
└── archived-docs/                    # Archived/legacy docs
```

---

## Support

**Troubleshooting:**
- See [USER-GUIDE.md - Troubleshooting](USER-GUIDE.md#troubleshooting)
- Check logs: `docker logs kafka-1`
- Check Kafka UI: http://localhost:8080

**Documentation:**
- Apache Kafka: https://kafka.apache.org/documentation/
- Kafka UI: https://docs.kafka-ui.provectus.io/

---

**Project Version:** 2.0  
**Last Updated:** 2025-10-30  
**Status:** ✅ Production Ready
