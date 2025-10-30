# JMX Access Guide

## Understanding JMX Ports

**JMX (Java Management Extensions)** uses **RMI protocol**, not HTTP. This means:
- ❌ You **cannot** open it in a web browser (http://localhost:9999 won't work)
- ✅ You **can** connect using JMX-compatible tools

## JMX Ports in this Cluster

| Broker  | JMX Port |
|---------|----------|
| kafka-1 | 9999     |
| kafka-2 | 10000    |
| kafka-3 | 10001    |

## How to Access JMX Metrics

### Option 1: JConsole (Easiest - Comes with Java)

**Requirements**: Java JDK installed on your machine

**Steps**:
```bash
# Open JConsole
jconsole localhost:9999
```

**What you'll see**:
- Overview tab: CPU, Heap, Threads, Classes
- Memory tab: Heap and Non-Heap memory usage with graphs
- Threads tab: Live thread monitoring
- MBeans tab: Browse all Kafka metrics
  - Navigate to: `kafka.server` → `BrokerTopicMetrics`
  - View metrics like: MessagesInPerSec, BytesInPerSec, etc.

**Screenshot workflow**:
1. Launch jconsole
2. Enter `localhost:9999` in the Remote Process field
3. Click "Connect"
4. If security warning appears, click "Insecure connection"

---

### Option 2: VisualVM (More Advanced)

**Download**: https://visualvm.github.io/download.html

**Steps**:
1. Install VisualVM
2. File → Add JMX Connection
3. Connection: `localhost:9999`
4. Display Name: `Kafka Broker 1`
5. Click OK

**Features**:
- Real-time monitoring
- CPU and Memory profiling
- Thread dumps
- Heap dumps
- MBean browser

---

### Option 3: Command-Line JMX Tool

**Query specific metrics**:

```bash
# Messages per second
docker exec kafka-1 kafka-run-class kafka.tools.JmxTool \
  --object-name kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec \
  --attributes Count \
  --jmx-url service:jmx:rmi:///jndi/rmi://localhost:9999/jmxrmi

# Bytes in per second
docker exec kafka-1 kafka-run-class kafka.tools.JmxTool \
  --object-name kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec \
  --attributes Count \
  --jmx-url service:jmx:rmi:///jndi/rmi://localhost:9999/jmxrmi

# Under-replicated partitions (should be 0)
docker exec kafka-1 kafka-run-class kafka.tools.JmxTool \
  --object-name kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions \
  --attributes Value \
  --jmx-url service:jmx:rmi:///jndi/rmi://localhost:9999/jmxrmi

# JVM Heap memory usage
docker exec kafka-1 kafka-run-class kafka.tools.JmxTool \
  --object-name java.lang:type=Memory \
  --attributes HeapMemoryUsage \
  --jmx-url service:jmx:rmi:///jndi/rmi://localhost:9999/jmxrmi
```

---

### Option 4: Prometheus + Grafana (For Dashboards)

If you want to visualize JMX metrics in a web browser dashboard like Kafka UI, you need to set up **Prometheus** and **Grafana**.

See `MONITORING.md` for complete setup instructions.

## Quick Verification

Test if JMX is working:

```bash
# Test connection
telnet localhost 9999

# If connected (you'll see "Connected to localhost"), JMX is working!
# Press Ctrl+] then type 'quit' to exit
```

Or use this simpler test:
```bash
docker exec kafka-1 bash -c 'echo "test" | nc -z localhost 9999 && echo "✓ JMX is accessible"'
```

## Common Use Cases

### 1. Monitor Broker Performance
```bash
# CPU and memory
jconsole localhost:9999
# Go to Overview tab
```

### 2. Check Message Rate
```bash
docker exec kafka-1 kafka-run-class kafka.tools.JmxTool \
  --object-name kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec \
  --jmx-url service:jmx:rmi:///jndi/rmi://localhost:9999/jmxrmi \
  --reporting-interval 5000
```

### 3. Monitor Replication Issues
```bash
docker exec kafka-1 kafka-run-class kafka.tools.JmxTool \
  --object-name kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions \
  --jmx-url service:jmx:rmi:///jndi/rmi://localhost:9999/jmxrmi
```

## Troubleshooting

### "Connection refused" error
```bash
# Verify JMX port is exposed
docker port kafka-1 | grep 9999

# Check if JMX is enabled in container
docker exec kafka-1 env | grep JMX

# Expected output:
# KAFKA_JMX_PORT=9999
# KAFKA_JMX_OPTS=-Dcom.sun.management.jmxremote ...
```

### "Cannot connect to localhost:9999"
```bash
# Check if port is listening
telnet localhost 9999

# Check firewall
sudo ss -tlnp | grep 9999

# Try connecting from within the container
docker exec kafka-1 bash -c 'echo "test" | nc -z localhost 9999'
```

## Summary

**For Web-Based Monitoring**: Use **http://localhost:8080** (Kafka UI) ← Easiest!

**For JMX Metrics**: 
- **GUI Tool**: JConsole (`jconsole localhost:9999`)
- **Command Line**: Kafka JmxTool (see examples above)
- **Advanced**: Prometheus + Grafana (requires setup)

**Remember**: JMX is NOT accessible via web browser. It requires JMX-compatible tools.
