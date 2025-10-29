# Production-Ready Kafka Cluster

A production-ready Apache Kafka cluster based on the "Building a Robust High‑Throughput Kafka Cluster (Bare-Metal Handbook)".

## Architecture

- **3 ZooKeeper nodes** for metadata management and coordination
- **3 Kafka brokers** with replication factor of 3
- **Rack-aware** replica placement for fault tolerance
- **Kafka UI** for monitoring and management
- Configured for **~100 MB/s throughput** (1,000 messages/sec @ 100KB each)

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Minimum 24GB RAM (8GB per broker)
- Minimum 100GB disk space

## 🚀 Quick Start

Get your production Kafka cluster running in 3 simple steps:

### Option 1: Using Make (Recommended)

The easiest way to start with automatic health checks and validation:

```bash
# Start the entire cluster with pre-flight checks
make start

# This will:
# ✓ Check Docker and Docker Compose are installed
# ✓ Verify available memory and disk space
# ✓ Pull latest images
# ✓ Start all services (3 ZooKeeper + 3 Kafka + UI)
# ✓ Wait for all services to be healthy
# ✓ Display connection information
```

**Total startup time: ~2-3 minutes**

### Option 2: Using Helper Scripts

```bash
# Start with validation
./scripts/start-cluster.sh
```

### Option 3: Using Docker Compose Directly

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

### Verify the Cluster is Running

```bash
# Run comprehensive health checks
make health

# Or manually check
docker-compose ps
```

All services should show status as **"Up (healthy)"**.

### Access Kafka UI

Open your browser and navigate to:
```
http://localhost:8080
```

You'll see the Kafka UI dashboard with:
- 3 brokers online
- Cluster overview
- Topic management
- Consumer group monitoring

### Connect Your Application

**From your host machine:**
```
localhost:9092,localhost:9093,localhost:9094
```

**From another Docker container:**
```
kafka-1:19092,kafka-2:19093,kafka-3:19094
```

### Next Steps

```bash
# Create production-ready topics
make topics

# Run performance test (validates 100 MB/s throughput)
make test

# View logs
make logs

# Stop cluster
make stop
```

That's it! Your production Kafka cluster is ready to use.

## Configuration Highlights

### Replication Settings
- **Replication Factor**: 3 (data replicated across all brokers)
- **Min In-Sync Replicas**: 2 (requires 2 brokers to acknowledge writes)
- **Tolerates**: Up to 1 broker failure without data loss

### Performance Tuning
- **Compression**: LZ4 (best balance of speed and compression ratio)
- **Network Threads**: 8 per broker
- **I/O Threads**: 8 per broker
- **Log Segment Size**: 1GB
- **Socket Buffers**: 1MB send/receive

### JVM Configuration
- **Heap Size**: 8GB (configurable via KAFKA_HEAP_SIZE)
- **GC**: G1GC with tuned pause times
- **Max GC Pause**: 20ms target

## Topic Creation

Create a production topic with proper configuration:

```bash
docker exec kafka-1 kafka-topics --create \
  --bootstrap-server kafka-1:19092 \
  --topic my-production-topic \
  --partitions 12 \
  --replication-factor 3 \
  --config min.insync.replicas=2 \
  --config compression.type=lz4 \
  --config retention.ms=604800000
```

### Recommended Partition Count
- **Formula**: (# brokers × # cores per broker) 
- **Example**: 3 brokers × 4 cores = 12 partitions
- Adjust based on throughput requirements and consumer parallelism

## Testing the Cluster

### 1. Produce Test Messages

```bash
docker exec -it kafka-1 kafka-console-producer \
  --bootstrap-server kafka-1:19092 \
  --topic my-production-topic \
  --producer-property acks=all \
  --producer-property compression.type=lz4
```

### 2. Consume Test Messages

```bash
docker exec -it kafka-1 kafka-console-consumer \
  --bootstrap-server kafka-1:19092 \
  --topic my-production-topic \
  --from-beginning \
  --group test-consumer-group
```

### 3. Performance Test

```bash
# Producer Performance Test (100 MB/s target)
docker exec kafka-1 kafka-producer-perf-test \
  --topic my-production-topic \
  --num-records 10000 \
  --record-size 102400 \
  --throughput 1000 \
  --producer-props \
    bootstrap.servers=kafka-1:19092,kafka-2:19093,kafka-3:19094 \
    acks=all \
    compression.type=lz4 \
    linger.ms=100 \
    batch.size=1048576

# Consumer Performance Test
docker exec kafka-1 kafka-consumer-perf-test \
  --topic my-production-topic \
  --bootstrap-server kafka-1:19092 \
  --messages 10000 \
  --threads 12 \
  --group perf-consumer-group
```

## Monitoring

### Check Cluster Health

```bash
# List all topics
docker exec kafka-1 kafka-topics --list \
  --bootstrap-server kafka-1:19092

# Describe cluster
docker exec kafka-1 kafka-broker-api-versions \
  --bootstrap-server kafka-1:19092,kafka-2:19093,kafka-3:19094

# Check consumer groups
docker exec kafka-1 kafka-consumer-groups --list \
  --bootstrap-server kafka-1:19092

# Describe consumer group lag
docker exec kafka-1 kafka-consumer-groups --describe \
  --bootstrap-server kafka-1:19092 \
  --group <your-consumer-group>
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific broker
docker-compose logs -f kafka-1

# ZooKeeper
docker-compose logs -f zookeeper-1
```

### Key Metrics to Monitor
- **Under-replicated partitions** (should be 0)
- **ISR shrink rate** (should be low)
- **Request latency** (p99 should be < 100ms)
- **Network utilization** (should be < 70%)
- **Disk utilization** (should be < 80%)
- **CPU usage** (should be < 70% average)

## Maintenance Operations

### Rolling Restart

```bash
# Restart one broker at a time (wait for it to be healthy before next)
docker-compose restart kafka-1
sleep 30
docker-compose restart kafka-2
sleep 30
docker-compose restart kafka-3
```

### Scale Out (Add Broker)

1. Add new broker to `docker-compose.yml`
2. Start the new broker:
```bash
docker-compose up -d kafka-4
```
3. Reassign partitions to include the new broker

### Backup ZooKeeper Data

```bash
docker exec zookeeper-1 tar czf /tmp/zk-backup.tar.gz /var/lib/zookeeper
docker cp zookeeper-1:/tmp/zk-backup.tar.gz ./backups/
```

## Troubleshooting

### Broker Not Starting

```bash
# Check logs
docker-compose logs kafka-1

# Common issues:
# 1. Insufficient memory - adjust KAFKA_HEAP_SIZE in .env
# 2. ZooKeeper not ready - ensure all ZK nodes are healthy
# 3. Port conflicts - check if ports are already in use
```

### Under-Replicated Partitions

```bash
# Check partition status
docker exec kafka-1 kafka-topics --describe \
  --bootstrap-server kafka-1:19092 \
  --under-replicated-partitions

# Common causes:
# 1. Broker down - check docker-compose ps
# 2. Network issues - check connectivity between brokers
# 3. Disk full - check docker volume usage
```

### High Latency

1. Check CPU/memory usage: `docker stats`
2. Check disk I/O: Look for throttling in logs
3. Verify network connectivity between brokers
4. Review JVM GC logs for long pauses

## Production Checklist

- [ ] Adjust heap size based on available memory (8GB minimum)
- [ ] Configure external access for clients outside Docker
- [ ] Set up persistent volume mounts for production data
- [ ] Enable SSL/TLS for encrypted communication
- [ ] Configure SASL authentication for security
- [ ] Set up monitoring with Prometheus + Grafana
- [ ] Configure log aggregation (ELK stack)
- [ ] Set up alerting for critical metrics
- [ ] Document disaster recovery procedures
- [ ] Schedule regular backups
- [ ] Test failover scenarios

## Security Considerations

This setup uses PLAINTEXT for simplicity. For production:

1. **Enable SSL/TLS**:
   - Generate certificates for each broker
   - Configure SSL listeners
   - Update client configurations

2. **Enable SASL Authentication**:
   - Configure SASL mechanism (SCRAM, PLAIN, or GSSAPI)
   - Create user credentials
   - Set ACLs for topic access

3. **Network Security**:
   - Use firewall rules to restrict access
   - Place Kafka cluster in private network
   - Use VPN for remote access

## Resource Requirements

### Minimum (Development/Testing)
- 3 vCPUs per broker
- 4GB RAM per broker
- 20GB disk per broker

### Recommended (Production)
- 8 vCPUs per broker
- 8GB heap + 8GB page cache = 16GB RAM per broker
- 500GB SSD/NVMe per broker
- 10 GbE network interface

### Optimal (High Throughput)
- 16 vCPUs per broker
- 8GB heap + 24GB page cache = 32GB RAM per broker
- 1TB+ NVMe per broker
- 10 GbE or higher network

## Support and References

Based on Apache Kafka best practices and the handbook recommendations:
- Min 3 brokers for production
- Replication factor of 3
- Min in-sync replicas of 2
- Rack-aware replica placement
- Proper JVM tuning with G1GC
- Adequate socket buffers for network throughput

## Shutdown

### Graceful Shutdown
```bash
docker-compose down
```

### Shutdown and Remove Volumes (DATA LOSS!)
```bash
docker-compose down -v
```

## License

This configuration is provided as-is for production use. Adjust based on your specific requirements.
