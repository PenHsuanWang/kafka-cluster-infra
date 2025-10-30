# Complete Monitoring Setup Guide

> **Target Audience:** DevOps Engineers, System Administrators, Site Reliability Engineers  
> **Last Updated:** 2025-10-30  
> **Version:** 1.0

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Quick Start](#quick-start)
3. [Monitoring Stack Setup](#monitoring-stack-setup)
4. [Metrics Collection](#metrics-collection)
5. [Dashboards](#dashboards)
6. [Alerting Rules](#alerting-rules)
7. [Log Aggregation](#log-aggregation)
8. [Performance Monitoring](#performance-monitoring)

---

## Architecture Overview

### Monitoring Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Monitoring Stack                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Kafka UI   │    │  Prometheus  │    │   Grafana    │  │
│  │  Port 8080   │    │  Port 9090   │    │  Port 3000   │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                    │                    │          │
│         │                    │                    │          │
│  ┌──────▼──────────────────┴────────────────────▼───────┐  │
│  │              JMX Exporters (per broker)               │  │
│  │        kafka-1:9999, kafka-2:10000, kafka-3:10001    │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                   │
│  ┌──────────────────────▼───────────────────────────────┐  │
│  │          Kafka Cluster (3 Brokers + 3 ZK)            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │      Elasticsearch + Logstash + Kibana (ELK)         │  │
│  │              (Optional - For Log Analysis)            │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Monitoring Layers

1. **Infrastructure Layer:** Docker, host metrics
2. **Application Layer:** Kafka broker metrics, JVM metrics
3. **Business Layer:** Topic metrics, consumer lag, throughput
4. **Log Layer:** Application logs, audit logs

---

## Quick Start

### 1. Basic Monitoring (Already Available)

**Kafka UI** - Web-based cluster management

```bash
# Access URL
open http://localhost:8080

# Features:
# - Broker health and metrics
# - Topic management and visualization
# - Consumer group monitoring
# - Message browsing
# - Cluster configuration
```

**Health Checks** - Automated validation

```bash
# Run health check
make health

# Or directly
./scripts/health-check.sh
```

**JMX Monitoring** - Direct broker metrics

```bash
# Connect with JConsole
jconsole localhost:9999

# Query specific metrics
docker exec kafka-1 kafka-run-class kafka.tools.JmxTool \
  --object-name kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec \
  --jmx-url service:jmx:rmi:///jndi/rmi://localhost:9999/jmxrmi \
  --reporting-interval 5000
```

### 2. Advanced Monitoring Setup

Follow sections below to set up Prometheus + Grafana for comprehensive monitoring.

---

## Monitoring Stack Setup

### Option 1: Prometheus + Grafana (Recommended)

#### Step 1: Create Prometheus Configuration

```bash
mkdir -p config/prometheus
cat > config/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'kafka-production'
    environment: 'docker'

# Alerting configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          # - 'alertmanager:9093'

# Load rules once and periodically evaluate them
rule_files:
  - "alert_rules.yml"

# Scrape configurations
scrape_configs:
  # Kafka JMX Exporter metrics
  - job_name: 'kafka-jmx'
    static_configs:
      - targets:
        - 'kafka-1:9999'
        - 'kafka-2:10000'
        - 'kafka-3:10001'
        labels:
          env: 'production'
          cluster: 'kafka-cluster-1'

  # JMX Exporter (standalone)
  - job_name: 'jmx-exporter'
    static_configs:
      - targets:
        - 'jmx-exporter:5556'

  # Kafka UI metrics (if exposed)
  - job_name: 'kafka-ui'
    metrics_path: '/actuator/prometheus'
    static_configs:
      - targets:
        - 'kafka-ui:8080'

  # Docker container metrics (if cAdvisor is added)
  - job_name: 'docker'
    static_configs:
      - targets:
        - 'cadvisor:8080'

  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets:
        - 'localhost:9090'
EOF
```

#### Step 2: Create Alert Rules

```bash
cat > config/prometheus/alert_rules.yml << 'EOF'
groups:
  - name: kafka_alerts
    interval: 30s
    rules:
      # Broker Alerts
      - alert: KafkaBrokerDown
        expr: up{job="kafka-jmx"} == 0
        for: 1m
        labels:
          severity: critical
          component: kafka
        annotations:
          summary: "Kafka broker {{ $labels.instance }} is down"
          description: "Broker has been down for more than 1 minute"

      - alert: KafkaUnderReplicatedPartitions
        expr: kafka_server_replicamanager_underreplicatedpartitions > 0
        for: 5m
        labels:
          severity: warning
          component: kafka
        annotations:
          summary: "Kafka has under-replicated partitions"
          description: "{{ $value }} partitions are under-replicated on {{ $labels.instance }}"

      - alert: KafkaOfflinePartitions
        expr: kafka_controller_kafkacontroller_offlinepartitionscount > 0
        for: 1m
        labels:
          severity: critical
          component: kafka
        annotations:
          summary: "Kafka has offline partitions"
          description: "{{ $value }} partitions are offline"

      # Performance Alerts
      - alert: KafkaHighProducerLatency
        expr: kafka_network_requestmetrics_totaltimems{request="Produce",quantile="0.99"} > 500
        for: 5m
        labels:
          severity: warning
          component: kafka
        annotations:
          summary: "High producer latency on {{ $labels.instance }}"
          description: "P99 latency is {{ $value }}ms (threshold: 500ms)"

      - alert: KafkaHighConsumerLag
        expr: kafka_consumergroup_lag > 10000
        for: 5m
        labels:
          severity: warning
          component: kafka
        annotations:
          summary: "High consumer lag for group {{ $labels.group }}"
          description: "Consumer lag is {{ $value }} messages"

      # Resource Alerts
      - alert: KafkaHighCPU
        expr: rate(process_cpu_seconds_total{job="kafka-jmx"}[5m]) * 100 > 80
        for: 10m
        labels:
          severity: warning
          component: kafka
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"
          description: "CPU usage is {{ $value }}%"

      - alert: KafkaHighMemory
        expr: (jvm_memory_bytes_used / jvm_memory_bytes_max) * 100 > 85
        for: 5m
        labels:
          severity: warning
          component: kafka
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is {{ $value }}%"

      - alert: KafkaHighDiskUsage
        expr: (1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100 > 85
        for: 5m
        labels:
          severity: critical
          component: kafka
        annotations:
          summary: "High disk usage on {{ $labels.instance }}"
          description: "Disk usage is {{ $value }}%"

      # JVM Alerts
      - alert: KafkaFrequentGC
        expr: rate(jvm_gc_collection_seconds_count[5m]) > 2
        for: 5m
        labels:
          severity: warning
          component: kafka
        annotations:
          summary: "Frequent GC on {{ $labels.instance }}"
          description: "GC happening {{ $value }} times per second"

      - alert: KafkaLongGCPauses
        expr: rate(jvm_gc_collection_seconds_sum[5m]) / rate(jvm_gc_collection_seconds_count[5m]) > 1
        for: 5m
        labels:
          severity: critical
          component: kafka
        annotations:
          summary: "Long GC pauses on {{ $labels.instance }}"
          description: "Average GC pause is {{ $value }} seconds"
EOF
```

#### Step 3: Add Prometheus to Docker Compose

```bash
cat >> docker-compose.yml << 'EOF'

  # Prometheus for metrics collection
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    hostname: prometheus
    networks:
      - kafka-network
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./config/prometheus/alert_rules.yml:/etc/prometheus/alert_rules.yml:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'
    restart: unless-stopped
    depends_on:
      - kafka-1
      - kafka-2
      - kafka-3

  # Grafana for visualization
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    hostname: grafana
    networks:
      - kafka-network
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
      - GF_SERVER_ROOT_URL=http://localhost:3000
    volumes:
      - grafana-data:/var/lib/grafana
      - ./config/grafana/provisioning:/etc/grafana/provisioning:ro
    restart: unless-stopped
    depends_on:
      - prometheus

volumes:
  prometheus-data:
    driver: local
  grafana-data:
    driver: local
EOF
```

#### Step 4: Create Grafana Provisioning

```bash
mkdir -p config/grafana/provisioning/datasources
mkdir -p config/grafana/provisioning/dashboards

# Datasource configuration
cat > config/grafana/provisioning/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

# Dashboard configuration
cat > config/grafana/provisioning/dashboards/kafka.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'Kafka Dashboards'
    orgId: 1
    folder: 'Kafka'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards/json
EOF
```

#### Step 5: Start Monitoring Stack

```bash
# Start Prometheus and Grafana
docker-compose up -d prometheus grafana

# Wait for services to start
sleep 30

# Verify Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# Access Grafana
open http://localhost:3000
# Login: admin / admin
```

---

## Metrics Collection

### Key Metrics to Monitor

#### 1. Broker Metrics

```yaml
# Throughput Metrics
kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec
kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec
kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec

# Request Metrics
kafka.network:type=RequestMetrics,name=TotalTimeMs,request=Produce
kafka.network:type=RequestMetrics,name=TotalTimeMs,request=FetchConsumer
kafka.network:type=RequestMetrics,name=RequestsPerSec,request=Produce

# Replica Metrics
kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions
kafka.server:type=ReplicaManager,name=IsrShrinksPerSec
kafka.server:type=ReplicaManager,name=IsrExpandsPerSec
kafka.server:type=ReplicaManager,name=PartitionCount
kafka.server:type=ReplicaManager,name=LeaderCount

# Controller Metrics
kafka.controller:type=KafkaController,name=OfflinePartitionsCount
kafka.controller:type=KafkaController,name=ActiveControllerCount

# Log Metrics
kafka.log:type=Log,name=Size,topic=*,partition=*
kafka.log:type=Log,name=NumLogSegments,topic=*,partition=*
```

#### 2. JVM Metrics

```yaml
# Memory
java.lang:type=Memory:HeapMemoryUsage
java.lang:type=Memory:NonHeapMemoryUsage

# Garbage Collection
java.lang:type=GarbageCollector,name=*:CollectionCount
java.lang:type=GarbageCollector,name=*:CollectionTime

# Threads
java.lang:type=Threading:ThreadCount
java.lang:type=Threading:DaemonThreadCount
```

#### 3. Consumer Metrics

```yaml
# Consumer Group Lag
kafka.consumer:type=consumer-fetch-manager-metrics,client-id=*:records-lag
kafka.consumer:type=consumer-fetch-manager-metrics,client-id=*:records-lag-max

# Consumer Throughput
kafka.consumer:type=consumer-fetch-manager-metrics,client-id=*:fetch-rate
kafka.consumer:type=consumer-fetch-manager-metrics,client-id=*:bytes-consumed-rate
```

### Metrics Collection Script

```bash
cat > scripts/collect-all-metrics.sh << 'EOF'
#!/bin/bash
# Comprehensive metrics collection script

OUTPUT_DIR="metrics/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_DIR"

echo "Collecting comprehensive metrics..."

# 1. Broker Metrics
echo "Collecting broker metrics..."
for broker in kafka-1 kafka-2 kafka-3; do
  port=$([[ $broker == "kafka-1" ]] && echo 9999 || [[ $broker == "kafka-2" ]] && echo 10000 || echo 10001)
  
  docker exec $broker kafka-run-class kafka.tools.JmxTool \
    --object-name kafka.server:type=BrokerTopicMetrics,name=* \
    --jmx-url service:jmx:rmi:///jndi/rmi://localhost:${port}/jmxrmi \
    --reporting-interval 1000 \
    --date-format yyyy-MM-dd_HH:mm:ss > "$OUTPUT_DIR/${broker}-broker-metrics.csv" &
done

# 2. Resource Usage
echo "Collecting resource usage..."
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" \
  > "$OUTPUT_DIR/resource-usage.txt"

# 3. Topic Descriptions
echo "Collecting topic information..."
docker exec kafka-1 kafka-topics --describe \
  --bootstrap-server kafka-1:19092 \
  > "$OUTPUT_DIR/topics.txt"

# 4. Consumer Group Status
echo "Collecting consumer group information..."
for group in $(docker exec kafka-1 kafka-consumer-groups --list --bootstrap-server kafka-1:19092); do
  docker exec kafka-1 kafka-consumer-groups --describe \
    --bootstrap-server kafka-1:19092 \
    --group $group \
    > "$OUTPUT_DIR/consumer-group-${group}.txt"
done

# 5. Cluster Health
echo "Collecting cluster health..."
./scripts/health-check.sh > "$OUTPUT_DIR/health-check.txt"

echo "Metrics collected in $OUTPUT_DIR"
EOF

chmod +x scripts/collect-all-metrics.sh
```

---

## Dashboards

### Kafka Overview Dashboard (Grafana)

Create a comprehensive Kafka monitoring dashboard:

```bash
mkdir -p config/grafana/provisioning/dashboards/json
cat > config/grafana/provisioning/dashboards/json/kafka-overview.json << 'EOF'
{
  "dashboard": {
    "title": "Kafka Cluster Overview",
    "tags": ["kafka", "monitoring"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Broker Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job='kafka-jmx'}",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "id": 2,
        "title": "Messages In Per Second",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(kafka_server_brokertopicmetrics_messagesin_total[5m])",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "id": 3,
        "title": "Bytes In Per Second",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(kafka_server_brokertopicmetrics_bytesin_total[5m])",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "id": 4,
        "title": "Under-Replicated Partitions",
        "type": "graph",
        "targets": [
          {
            "expr": "kafka_server_replicamanager_underreplicatedpartitions",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "id": 5,
        "title": "Request Latency (P99)",
        "type": "graph",
        "targets": [
          {
            "expr": "kafka_network_requestmetrics_totaltimems{quantile='0.99'}",
            "legendFormat": "{{request}} - {{instance}}"
          }
        ]
      },
      {
        "id": 6,
        "title": "JVM Heap Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "(jvm_memory_bytes_used{area='heap'} / jvm_memory_bytes_max{area='heap'}) * 100",
            "legendFormat": "{{instance}}"
          }
        ]
      }
    ]
  }
}
EOF
```

### Import Pre-Built Dashboards

```bash
# Kafka Exporter Dashboard (ID: 7589)
# Strimzi Kafka Dashboard (ID: 11962)
# JVM Dashboard (ID: 11965)

# Import via Grafana UI:
# 1. Go to http://localhost:3000
# 2. Click "+" → "Import"
# 3. Enter Dashboard ID: 7589
# 4. Select Prometheus datasource
# 5. Click "Import"
```

---

## Alerting Rules

### AlertManager Setup (Optional)

```bash
mkdir -p config/alertmanager
cat > config/alertmanager/alertmanager.yml << 'EOF'
global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@yourcompany.com'
  smtp_auth_username: 'alerts@yourcompany.com'
  smtp_auth_password: 'your-password'

route:
  group_by: ['alertname', 'cluster', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'email-notifications'
  
  routes:
  - match:
      severity: critical
    receiver: 'pagerduty'
    continue: true
  
  - match:
      severity: warning
    receiver: 'email-notifications'

receivers:
- name: 'email-notifications'
  email_configs:
  - to: 'team@yourcompany.com'
    headers:
      Subject: 'Kafka Alert: {{ .GroupLabels.alertname }}'
    html: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

- name: 'pagerduty'
  pagerduty_configs:
  - service_key: 'your-pagerduty-key'
    description: '{{ .GroupLabels.alertname }}'
    
- name: 'slack'
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    channel: '#kafka-alerts'
    title: 'Kafka Alert'
    text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'instance']
EOF
```

### Add AlertManager to Docker Compose

```bash
cat >> docker-compose.yml << 'EOF'

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    hostname: alertmanager
    networks:
      - kafka-network
    ports:
      - "9093:9093"
    volumes:
      - ./config/alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
      - alertmanager-data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    restart: unless-stopped

volumes:
  alertmanager-data:
    driver: local
EOF
```

---

## Log Aggregation

### Option 1: ELK Stack (Elasticsearch, Logstash, Kibana)

```yaml
# Add to docker-compose.yml
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.10.0
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
    networks:
      - kafka-network

  logstash:
    image: docker.elastic.co/logstash/logstash:8.10.0
    container_name: logstash
    volumes:
      - ./config/logstash/logstash.conf:/usr/share/logstash/pipeline/logstash.conf:ro
    ports:
      - "5000:5000"
    networks:
      - kafka-network
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.10.0
    container_name: kibana
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    networks:
      - kafka-network
    depends_on:
      - elasticsearch

volumes:
  elasticsearch-data:
    driver: local
```

### Option 2: Loki + Promtail (Lightweight Alternative)

```yaml
# Add to docker-compose.yml
  loki:
    image: grafana/loki:latest
    container_name: loki
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - kafka-network
    volumes:
      - loki-data:/loki

  promtail:
    image: grafana/promtail:latest
    container_name: promtail
    volumes:
      - /var/log:/var/log:ro
      - ./config/promtail/promtail.yml:/etc/promtail/config.yml:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    command: -config.file=/etc/promtail/config.yml
    networks:
      - kafka-network
    depends_on:
      - loki

volumes:
  loki-data:
    driver: local
```

---

## Performance Monitoring

### Real-Time Performance Dashboard

Access monitoring dashboards:

```bash
# Kafka UI (Primary)
open http://localhost:8080

# Grafana (Advanced Metrics)
open http://localhost:3000

# Prometheus (Raw Metrics & Alerts)
open http://localhost:9090

# Kibana (Logs)
open http://localhost:5601
```

### Monitoring Checklist

**Daily Checks:**
- [ ] All brokers healthy
- [ ] No under-replicated partitions
- [ ] Consumer lag within limits
- [ ] CPU usage < 70%
- [ ] Memory usage < 80%
- [ ] Disk usage < 80%

**Weekly Checks:**
- [ ] Review performance trends
- [ ] Check log growth
- [ ] Verify backup procedures
- [ ] Review alert history
- [ ] Capacity planning review

**Monthly Checks:**
- [ ] Performance test execution
- [ ] Security audit
- [ ] Disaster recovery test
- [ ] Documentation update
- [ ] Dependency updates

---

## Monitoring URLs Quick Reference

| Service | URL | Default Credentials | Purpose |
|---------|-----|-------------------|---------|
| Kafka UI | http://localhost:8080 | - | Cluster management |
| Grafana | http://localhost:3000 | admin/admin | Dashboards |
| Prometheus | http://localhost:9090 | - | Metrics & Alerts |
| AlertManager | http://localhost:9093 | - | Alert routing |
| Kibana | http://localhost:5601 | - | Log analysis |
| JMX (kafka-1) | localhost:9999 | - | Direct JMX |
| JMX (kafka-2) | localhost:10000 | - | Direct JMX |
| JMX (kafka-3) | localhost:10001 | - | Direct JMX |

---

**Document Version:** 1.0  
**Last Review:** 2025-10-30  
**Next Review:** Quarterly or after major changes
