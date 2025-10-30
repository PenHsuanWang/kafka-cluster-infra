# Kafka Cluster Monitoring Guide

## Overview

This Kafka cluster includes two monitoring solutions:

1. **Kafka UI** (Primary) - Web-based dashboard at `http://localhost:8080`
2. **JMX Metrics** - Prometheus-compatible metrics exposed on each broker

## Kafka UI Dashboard

### Access
```
http://localhost:8080
```

### Features
- **Cluster Overview**: Real-time view of all 3 brokers
- **Topic Management**: Create, view, and manage topics
- **Consumer Groups**: Monitor consumer lag and performance
- **Messages**: Browse and search messages
- **Broker Metrics**: CPU, memory, disk usage per broker
- **Configuration**: View and edit broker/topic configurations

### Quick Checks
- Verify all 3 brokers are online and healthy
- Check topic replication status
- Monitor consumer group lag
- View partition distribution across brokers

## JMX Metrics (Advanced)

### JMX Ports
Each Kafka broker exposes JMX metrics on these ports:

| Broker | Internal JMX Port | External Host Port |
|--------|------------------|--------------------|
| kafka-1 | 9999 | 9999 |
| kafka-2 | 9999 | 10000 |
| kafka-3 | 9999 | 10001 |

### Testing JMX Connectivity

```bash
# Test from within Docker network
docker exec kafka-1 bash -c 'echo "test" | nc -z localhost 9999 && echo "JMX is open"'

# Test from host
telnet localhost 9999
```

### Accessing JMX Metrics

#### Option 1: Using JConsole
```bash
jconsole localhost:9999
```

#### Option 2: Using JMX Exporter (Prometheus)
The cluster includes a JMX exporter at:
```
http://localhost:5556/metrics
```

**Note**: The JMX exporter requires additional configuration to scrape metrics from Kafka brokers. See "Setting up JMX Exporter" below.

## Setting up JMX Exporter (Optional)

If you want to collect Prometheus metrics, you need to configure the JMX exporter properly:

### Current Configuration
The JMX exporter configuration is located at:
```
config/jmx-exporter-config.yml
```

### Integration with Prometheus

1. **Add Prometheus** to docker-compose.yml:
```yaml
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    networks:
      - kafka-network
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    restart: unless-stopped
```

2. **Create** `config/prometheus.yml`:
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'kafka-jmx'
    static_configs:
      - targets:
        - 'kafka-1:9999'
        - 'kafka-2:9999'
        - 'kafka-3:9999'
```

3. **Access Prometheus**:
```
http://localhost:9090
```

### Integration with Grafana

1. **Add Grafana** to docker-compose.yml:
```yaml
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    networks:
      - kafka-network
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
    restart: unless-stopped

volumes:
  grafana-data:
    driver: local
```

2. **Access Grafana**:
```
http://localhost:3000
Username: admin
Password: admin
```

3. **Import Kafka Dashboard**:
   - Add Prometheus as data source (http://prometheus:9090)
   - Import dashboard ID: 7589 (Kafka Overview)

## Key Metrics to Monitor

### Broker Health
- **Under-replicated partitions**: Should be 0
- **Offline partitions**: Should be 0
- **Active controller count**: Should be 1 (across cluster)
- **Leader count**: Should be balanced across brokers

### Performance Metrics
- **Request latency** (p99): < 100ms recommended
- **Bytes in/out per second**: Monitor throughput
- **Messages in per second**: Track message rate
- **Network processor idle %**: Should be > 30%
- **Request handler idle %**: Should be > 30%

### Resource Usage
- **JVM heap memory usage**: < 80% recommended
- **GC pause time**: < 100ms for p99
- **Disk usage**: < 80% recommended
- **CPU usage**: < 70% average

### Replication
- **ISR shrink rate**: Should be low
- **ISR expand rate**: Should be low  
- **Replica lag**: Should be near 0

## Command-Line Monitoring

### Check Cluster Health
```bash
docker exec kafka-1 kafka-broker-api-versions \
  --bootstrap-server kafka-1:19092,kafka-2:19093,kafka-3:19094
```

### List Topics
```bash
docker exec kafka-1 kafka-topics --list \
  --bootstrap-server kafka-1:19092
```

### Describe Topic
```bash
docker exec kafka-1 kafka-topics --describe \
  --bootstrap-server kafka-1:19092 \
  --topic <topic-name>
```

### Check Consumer Group Lag
```bash
docker exec kafka-1 kafka-consumer-groups --describe \
  --bootstrap-server kafka-1:19092 \
  --group <group-name>
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific broker
docker-compose logs -f kafka-1

# Follow last 100 lines
docker-compose logs -f --tail=100 kafka-1
```

## Troubleshooting Monitoring

### Kafka UI Not Loading
```bash
# Check if container is running
docker-compose ps kafka-ui

# Check logs
docker-compose logs kafka-ui --tail=50

# Restart Kafka UI
docker-compose restart kafka-ui
```

### JMX Port Not Accessible
```bash
# Verify JMX is enabled
docker exec kafka-1 env | grep JMX

# Check if port is listening
docker exec kafka-1 bash -c 'echo "test" | nc -z localhost 9999 && echo "Open" || echo "Closed"'

# Check firewall rules on host
ss -tlnp | grep -E "9999|10000|10001"
```

### Missing Metrics in JMX Exporter
The JMX exporter at port 5556 requires additional configuration to properly connect to Kafka's JMX interface. For now, use **Kafka UI (port 8080)** as the primary monitoring tool, which provides comprehensive metrics and dashboards out-of-the-box.

## Alert Recommendations

Set up alerts for:
- Under-replicated partitions > 0
- Offline partitions > 0
- Consumer lag > threshold (e.g., 1000 messages)
- Broker CPU > 80%
- Broker disk > 85%
- JVM heap usage > 85%
- Request latency p99 > 200ms

## Summary

**For immediate monitoring needs**, use:
- **Kafka UI**: `http://localhost:8080` (Primary dashboard - works out-of-the-box)
- **Docker logs**: `docker-compose logs -f`
- **CLI tools**: kafka-topics, kafka-consumer-groups, etc.

**For advanced monitoring** (requires setup):
- **JMX**: Exposed on ports 9999, 10000, 10001
- **Prometheus + Grafana**: Requires additional configuration (see above)
