# Kafka Cluster - Complete Developer Guide

> **For:** Software Engineers, Application Developers  
> **Version:** 2.0  
> **Last Updated:** 2025-10-30

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Connection Configuration](#connection-configuration)
3. [Producer Development](#producer-development)
4. [Consumer Development](#consumer-development)
5. [Best Practices](#best-practices)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)
8. [Code Examples](#code-examples)

---

## Quick Start

### Prerequisites

1. **Cluster Running:**
   ```bash
   # Verify cluster is up
   docker-compose ps
   # All services should show "Up (healthy)"
   ```

2. **Connection Details:**
   - **From host machine:** `localhost:9092,localhost:9093,localhost:9094`
   - **From Docker network:** `kafka-1:19092,kafka-2:19093,kafka-3:19094`
   - **From external network:** Update `EXTERNAL_HOST` in `.env`

3. **Test Connectivity:**
   ```bash
   telnet localhost 9092
   # Should connect successfully
   ```

### 5-Minute Example

**Create a test topic:**
```bash
docker exec kafka-1 kafka-topics --create \
  --topic quickstart-events \
  --partitions 3 \
  --replication-factor 3 \
  --bootstrap-server kafka-1:19092
```

**Send a message:**
```bash
echo "key:value" | docker exec -i kafka-1 \
  kafka-console-producer --topic quickstart-events \
  --property "parse.key=true" \
  --property "key.separator=:" \
  --bootstrap-server kafka-1:19092
```

**Receive messages:**
```bash
docker exec kafka-1 kafka-console-consumer \
  --topic quickstart-events \
  --from-beginning \
  --property print.key=true \
  --property key.separator=: \
  --bootstrap-server kafka-1:19092
```

---

## Connection Configuration

### Bootstrap Servers

**Development (from host):**
```properties
bootstrap.servers=localhost:9092,localhost:9093,localhost:9094
```

**Containerized Apps (from Docker network):**
```properties
bootstrap.servers=kafka-1:19092,kafka-2:19093,kafka-3:19094
```

**Production (from external network):**
```properties
# Update EXTERNAL_HOST in .env first
bootstrap.servers=<external-ip>:9092,<external-ip>:9093,<external-ip>:9094
```

### Client IDs

Always set a meaningful client ID:
```properties
client.id=my-service-producer-001
```

Benefits:
- Easier troubleshooting
- Better monitoring
- Request tracking in logs

### Serializers/Deserializers

**Common Serializers:**
```java
// String
key.serializer=org.apache.kafka.common.serialization.StringSerializer
value.serializer=org.apache.kafka.common.serialization.StringSerializer

// Integer
key.serializer=org.apache.kafka.common.serialization.IntegerSerializer

// JSON (using custom serializer)
value.serializer=com.example.JsonSerializer

// Avro (with Schema Registry)
value.serializer=io.confluent.kafka.serializers.KafkaAvroSerializer
```

---

## Producer Development

### Configuration Recommendations

#### Reliable Producer (Recommended)

**For critical data where message loss is unacceptable:**

```properties
# Connection
bootstrap.servers=localhost:9092,localhost:9093,localhost:9094
client.id=my-reliable-producer

# Serialization
key.serializer=org.apache.kafka.common.serialization.StringSerializer
value.serializer=org.apache.kafka.common.serialization.StringSerializer

# Reliability
acks=all                                  # Wait for all in-sync replicas
retries=2147483647                        # Retry indefinitely
max.in.flight.requests.per.connection=5   # Max inflight requests
enable.idempotence=true                   # Prevent duplicates (exactly-once)
transactional.id=my-tx-producer-001       # For transactions (optional)

# Performance (still reliable)
compression.type=lz4                      # Fast compression
batch.size=16384                          # 16KB batches
linger.ms=10                              # 10ms batching delay
buffer.memory=33554432                    # 32MB buffer

# Timeouts
request.timeout.ms=30000                  # 30 seconds
delivery.timeout.ms=120000                # 2 minutes total
max.block.ms=60000                        # 1 minute blocking
```

#### High-Performance Producer

**For non-critical data prioritizing throughput:**

```properties
# Connection
bootstrap.servers=localhost:9092,localhost:9093,localhost:9094
client.id=my-fast-producer

# Serialization
key.serializer=org.apache.kafka.common.serialization.StringSerializer
value.serializer=org.apache.kafka.common.serialization.StringSerializer

# Performance
acks=1                                    # Leader only (faster)
compression.type=lz4                      # Fast compression
batch.size=32768                          # Larger batches (32KB)
linger.ms=50                              # More batching (50ms)
buffer.memory=67108864                    # More buffer (64MB)

# Less strict
retries=3                                 # Limited retries
max.in.flight.requests.per.connection=10  # More inflight
enable.idempotence=false                  # Not needed for logs/metrics
```

### Producer Patterns

#### 1. Fire-and-Forget (Fastest, Risk of Loss)

**Use for:** Logs, metrics, non-critical events

```java
import org.apache.kafka.clients.producer.*;
import java.util.Properties;

public class FireAndForgetProducer {
    public static void main(String[] args) {
        Properties props = new Properties();
        props.put("bootstrap.servers", "localhost:9092,localhost:9093,localhost:9094");
        props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        props.put("acks", "1");
        props.put("compression.type", "lz4");
        
        Producer<String, String> producer = new KafkaProducer<>(props);
        
        try {
            for (int i = 0; i < 100; i++) {
                ProducerRecord<String, String> record = 
                    new ProducerRecord<>("my-topic", "key-" + i, "value-" + i);
                producer.send(record);  // No callback, no waiting
            }
        } finally {
            producer.close();
        }
    }
}
```

#### 2. Async with Callback (Recommended)

**Use for:** Most applications - balances performance and reliability

```java
import org.apache.kafka.clients.producer.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class AsyncProducer {
    private static final Logger log = LoggerFactory.getLogger(AsyncProducer.class);
    
    public static void main(String[] args) {
        Properties props = new Properties();
        props.put("bootstrap.servers", "localhost:9092,localhost:9093,localhost:9094");
        props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        props.put("acks", "all");
        props.put("retries", Integer.MAX_VALUE);
        props.put("enable.idempotence", "true");
        props.put("compression.type", "lz4");
        
        Producer<String, String> producer = new KafkaProducer<>(props);
        
        try {
            for (int i = 0; i < 100; i++) {
                final int index = i;
                ProducerRecord<String, String> record = 
                    new ProducerRecord<>("my-topic", "key-" + i, "value-" + i);
                
                producer.send(record, new Callback() {
                    @Override
                    public void onCompletion(RecordMetadata metadata, Exception exception) {
                        if (exception != null) {
                            log.error("Failed to send message {}: {}", index, exception.getMessage());
                            // Handle error: retry, send to DLQ, alert, etc.
                        } else {
                            log.debug("Message {} sent to partition {} offset {}", 
                                index, metadata.partition(), metadata.offset());
                        }
                    }
                });
            }
        } finally {
            producer.close();  // Waits for inflight requests
        }
    }
}
```

#### 3. Synchronous Send (Slowest, Most Reliable)

**Use for:** Financial transactions, critical business events

```java
import org.apache.kafka.clients.producer.*;
import java.util.concurrent.ExecutionException;

public class SyncProducer {
    public static void main(String[] args) {
        Properties props = new Properties();
        props.put("bootstrap.servers", "localhost:9092,localhost:9093,localhost:9094");
        props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        props.put("acks", "all");
        props.put("enable.idempotence", "true");
        
        Producer<String, String> producer = new KafkaProducer<>(props);
        
        try {
            for (int i = 0; i < 100; i++) {
                ProducerRecord<String, String> record = 
                    new ProducerRecord<>("my-topic", "key-" + i, "value-" + i);
                
                try {
                    // Blocks until complete or error
                    RecordMetadata metadata = producer.send(record).get();
                    System.out.printf("Sent to partition %d offset %d%n",
                        metadata.partition(), metadata.offset());
                } catch (ExecutionException e) {
                    System.err.println("Send failed: " + e.getCause());
                    // Handle error appropriately
                }
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        } finally {
            producer.close();
        }
    }
}
```

#### 4. Transactional Producer (Exactly-Once)

**Use for:** Financial systems, database sync, critical state updates

```java
import org.apache.kafka.clients.producer.*;

public class TransactionalProducer {
    public static void main(String[] args) {
        Properties props = new Properties();
        props.put("bootstrap.servers", "localhost:9092,localhost:9093,localhost:9094");
        props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        props.put("acks", "all");
        props.put("enable.idempotence", "true");
        props.put("transactional.id", "my-transactional-producer-1");
        
        Producer<String, String> producer = new KafkaProducer<>(props);
        
        try {
            producer.initTransactions();
            
            producer.beginTransaction();
            try {
                for (int i = 0; i < 100; i++) {
                    ProducerRecord<String, String> record = 
                        new ProducerRecord<>("my-topic", "key-" + i, "value-" + i);
                    producer.send(record);
                }
                producer.commitTransaction();
                System.out.println("Transaction committed");
            } catch (Exception e) {
                producer.abortTransaction();
                System.err.println("Transaction aborted: " + e.getMessage());
                throw e;
            }
        } finally {
            producer.close();
        }
    }
}
```

### Partition Key Selection

**Good: Consistent hashing for ordering**
```java
// All events for same user go to same partition (maintains order)
ProducerRecord<String, String> record = 
    new ProducerRecord<>("orders", customerId, orderData);
```

**Bad: Random keys (breaks ordering)**
```java
// Each message goes to different partition (no order guarantee)
ProducerRecord<String, String> record = 
    new ProducerRecord<>("orders", UUID.randomUUID().toString(), orderData);
```

**Null key: Round-robin distribution**
```java
// Messages distributed evenly, no ordering
ProducerRecord<String, String> record = 
    new ProducerRecord<>("logs", null, logMessage);
```

### Error Handling

**Retry with Exponential Backoff:**
```java
int maxRetries = 3;
int baseDelay = 1000;  // 1 second

for (int retry = 0; retry < maxRetries; retry++) {
    try {
        producer.send(record).get();
        break;  // Success
    } catch (Exception e) {
        if (retry == maxRetries - 1) {
            // Final retry failed - send to dead letter queue
            sendToDeadLetterQueue(record, e);
            break;
        } else {
            long delay = baseDelay * (1L << retry);  // Exponential backoff
            Thread.sleep(delay);
        }
    }
}
```

---

## Consumer Development

### Configuration Recommendations

#### Reliable Consumer (At-Least-Once)

**For critical data processing:**

```properties
# Connection
bootstrap.servers=localhost:9092,localhost:9093,localhost:9094
group.id=my-consumer-group
client.id=my-consumer-001

# Serialization
key.deserializer=org.apache.kafka.common.serialization.StringDeserializer
value.deserializer=org.apache.kafka.common.serialization.StringDeserializer

# Reliability
enable.auto.commit=false                  # Manual commit
auto.offset.reset=earliest                # Start from beginning if no offset
isolation.level=read_committed            # Only read committed (for transactions)

# Performance
fetch.min.bytes=1024                      # Wait for 1KB
fetch.max.wait.ms=500                     # Or 500ms timeout
max.poll.records=500                      # Process 500 records per poll
max.poll.interval.ms=300000               # 5 minutes processing time

# Session Management
session.timeout.ms=10000                  # 10 seconds
heartbeat.interval.ms=3000                # 3 seconds
```

#### High-Performance Consumer

**For throughput-focused processing:**

```properties
# Connection
bootstrap.servers=localhost:9092,localhost:9093,localhost:9094
group.id=my-fast-consumer-group
client.id=my-fast-consumer-001

# Serialization
key.deserializer=org.apache.kafka.common.serialization.StringDeserializer
value.deserializer=org.apache.kafka.common.serialization.StringDeserializer

# Performance
enable.auto.commit=true                   # Auto commit (less reliable)
auto.commit.interval.ms=5000              # Commit every 5s
fetch.min.bytes=50000                     # Wait for more data
fetch.max.wait.ms=1000                    # Or 1s timeout
max.poll.records=2000                     # Larger batches

# Session
session.timeout.ms=30000                  # Longer timeout
heartbeat.interval.ms=10000               # Less frequent heartbeat
```

### Consumer Patterns

#### 1. Auto-Commit Consumer (Simplest)

**Use for:** Non-critical data, at-most-once processing

```java
import org.apache.kafka.clients.consumer.*;
import java.time.Duration;
import java.util.*;

public class AutoCommitConsumer {
    public static void main(String[] args) {
        Properties props = new Properties();
        props.put("bootstrap.servers", "localhost:9092,localhost:9093,localhost:9094");
        props.put("group.id", "my-group");
        props.put("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
        props.put("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
        props.put("enable.auto.commit", "true");
        props.put("auto.commit.interval.ms", "1000");
        
        Consumer<String, String> consumer = new KafkaConsumer<>(props);
        consumer.subscribe(Arrays.asList("my-topic"));
        
        try {
            while (true) {
                ConsumerRecords<String, String> records = 
                    consumer.poll(Duration.ofMillis(100));
                
                for (ConsumerRecord<String, String> record : records) {
                    System.out.printf("key=%s, value=%s, partition=%d, offset=%d%n",
                        record.key(), record.value(), record.partition(), record.offset());
                    
                    processRecord(record);
                }
            }
        } finally {
            consumer.close();
        }
    }
    
    private static void processRecord(ConsumerRecord<String, String> record) {
        // Your processing logic
    }
}
```

#### 2. Manual Commit Consumer (Recommended)

**Use for:** At-least-once processing with reliability

```java
import org.apache.kafka.clients.consumer.*;
import java.time.Duration;
import java.util.*;

public class ManualCommitConsumer {
    public static void main(String[] args) {
        Properties props = new Properties();
        props.put("bootstrap.servers", "localhost:9092,localhost:9093,localhost:9094");
        props.put("group.id", "my-group");
        props.put("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
        props.put("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
        props.put("enable.auto.commit", "false");
        
        Consumer<String, String> consumer = new KafkaConsumer<>(props);
        consumer.subscribe(Arrays.asList("my-topic"));
        
        try {
            while (true) {
                ConsumerRecords<String, String> records = 
                    consumer.poll(Duration.ofMillis(100));
                
                for (ConsumerRecord<String, String> record : records) {
                    try {
                        processRecord(record);
                        // Commit after successful processing
                        consumer.commitSync();
                    } catch (Exception e) {
                        System.err.println("Processing failed: " + e.getMessage());
                        // Don't commit - will reprocess on next poll
                    }
                }
            }
        } finally {
            consumer.close();
        }
    }
    
    private static void processRecord(ConsumerRecord<String, String> record) {
        // Your processing logic
        System.out.printf("Processing: %s%n", record.value());
    }
}
```

#### 3. Batch Processing Consumer

**Use for:** Bulk database inserts, batch analytics

```java
import org.apache.kafka.clients.consumer.*;
import java.time.Duration;
import java.util.*;

public class BatchConsumer {
    public static void main(String[] args) {
        Properties props = new Properties();
        props.put("bootstrap.servers", "localhost:9092,localhost:9093,localhost:9094");
        props.put("group.id", "batch-group");
        props.put("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
        props.put("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
        props.put("enable.auto.commit", "false");
        props.put("max.poll.records", "500");
        
        Consumer<String, String> consumer = new KafkaConsumer<>(props);
        consumer.subscribe(Arrays.asList("my-topic"));
        
        try {
            while (true) {
                ConsumerRecords<String, String> records = 
                    consumer.poll(Duration.ofMillis(1000));
                
                if (!records.isEmpty()) {
                    List<String> batch = new ArrayList<>();
                    for (ConsumerRecord<String, String> record : records) {
                        batch.add(record.value());
                    }
                    
                    try {
                        processBatch(batch);
                        consumer.commitSync();
                        System.out.printf("Processed batch of %d records%n", batch.size());
                    } catch (Exception e) {
                        System.err.println("Batch processing failed: " + e.getMessage());
                        // Seek back or implement retry logic
                    }
                }
            }
        } finally {
            consumer.close();
        }
    }
    
    private static void processBatch(List<String> batch) {
        // Bulk database insert or batch processing
        System.out.printf("Batch processing %d records%n", batch.size());
    }
}
```

#### 4. Multi-Threaded Consumer

**Use for:** High-throughput parallel processing

```java
import org.apache.kafka.clients.consumer.*;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.*;

public class MultiThreadedConsumer {
    private static final int NUM_THREADS = 4;
    
    public static void main(String[] args) {
        ExecutorService executor = Executors.newFixedThreadPool(NUM_THREADS);
        
        Properties props = new Properties();
        props.put("bootstrap.servers", "localhost:9092,localhost:9093,localhost:9094");
        props.put("group.id", "multi-threaded-group");
        props.put("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
        props.put("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
        props.put("enable.auto.commit", "false");
        
        for (int i = 0; i < NUM_THREADS; i++) {
            executor.submit(new ConsumerWorker(props, i));
        }
        
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.out.println("Shutting down...");
            executor.shutdownNow();
        }));
    }
    
    static class ConsumerWorker implements Runnable {
        private final Consumer<String, String> consumer;
        private final int workerId;
        
        public ConsumerWorker(Properties props, int workerId) {
            this.workerId = workerId;
            this.consumer = new KafkaConsumer<>(props);
            consumer.subscribe(Arrays.asList("my-topic"));
        }
        
        @Override
        public void run() {
            try {
                while (true) {
                    ConsumerRecords<String, String> records = 
                        consumer.poll(Duration.ofMillis(100));
                    
                    for (ConsumerRecord<String, String> record : records) {
                        System.out.printf("Worker %d: %s%n", workerId, record.value());
                        processRecord(record);
                    }
                    
                    if (!records.isEmpty()) {
                        consumer.commitSync();
                    }
                }
            } catch (Exception e) {
                System.err.printf("Worker %d error: %s%n", workerId, e.getMessage());
            } finally {
                consumer.close();
            }
        }
        
        private void processRecord(ConsumerRecord<String, String> record) {
            // Processing logic
        }
    }
}
```

---

## Best Practices

### Topic Design

**Naming Convention:**
```
# Good: Hierarchical, descriptive
events.user.registration
events.order.created
metrics.app.performance
logs.service.error

# Bad: Vague, flat
topic1
data
events
```

**Create Topics Explicitly:**
```bash
# Don't rely on auto-creation - define configuration explicitly
docker exec kafka-1 kafka-topics --create \
  --topic events.user.registration \
  --partitions 12 \
  --replication-factor 3 \
  --config min.insync.replicas=2 \
  --config compression.type=lz4 \
  --config retention.ms=604800000 \
  --bootstrap-server kafka-1:19092
```

### Message Design

**Use Keys for Ordering:**
```java
// All events for same entity maintain order
String key = customerId;  // Or orderId, userId, etc.
ProducerRecord<String, String> record = 
    new ProducerRecord<>("orders", key, orderData);
```

**Include Metadata:**
```json
{
  "schema_version": "1.0",
  "timestamp": "2025-10-30T12:34:56Z",
  "event_id": "uuid-here",
  "event_type": "order_created",
  "data": {
    "order_id": "12345",
    "amount": 99.99
  }
}
```

**Consider Message Size:**
- Keep messages < 1MB
- Use compression (LZ4 recommended)
- For large payloads, store in S3/blob storage and send reference

### Resource Management

**Always Close Resources:**
```java
// Use try-with-resources
try (Producer<String, String> producer = new KafkaProducer<>(props)) {
    producer.send(record);
} // Automatically closed

// Or explicit close in finally block
Producer<String, String> producer = null;
try {
    producer = new KafkaProducer<>(props);
    producer.send(record);
} finally {
    if (producer != null) {
        producer.close();
    }
}
```

**Reuse Producers:**
```java
// DON'T: Create new producer for each message
for (int i = 0; i < 1000; i++) {
    Producer<String, String> producer = new KafkaProducer<>(props);  // BAD!
    producer.send(record);
    producer.close();
}

// DO: Reuse single producer
Producer<String, String> producer = new KafkaProducer<>(props);
try {
    for (int i = 0; i < 1000; i++) {
        producer.send(record);
    }
} finally {
    producer.close();
}
```

### Error Handling

**Handle All Exceptions:**
```java
try {
    RecordMetadata metadata = producer.send(record).get();
} catch (TimeoutException e) {
    // Broker unavailable, network issue
    log.error("Send timeout", e);
    retry(record);
} catch (InterruptedException e) {
    Thread.currentThread().interrupt();
    throw e;
} catch (ExecutionException e) {
    Throwable cause = e.getCause();
    if (cause instanceof RecordTooLargeException) {
        log.error("Message too large", cause);
        // Don't retry - message is invalid
    } else if (cause instanceof TimeoutException) {
        log.error("Request timeout", cause);
        retry(record);
    } else {
        log.error("Unknown error", cause);
    }
}
```

### Security

**Don't Hardcode Credentials:**
```java
// BAD
props.put("bootstrap.servers", "prod-server:9092");
props.put("sasl.jaas.config", "org.apache.kafka.common.security.plain.PlainLoginModule required username='user' password='secret';");

// GOOD - Use environment variables or config files
String bootstrapServers = System.getenv("KAFKA_BOOTSTRAP_SERVERS");
String jaasConfig = System.getenv("KAFKA_JAAS_CONFIG");
props.put("bootstrap.servers", bootstrapServers);
props.put("sasl.jaas.config", jaasConfig);
```

---

## Testing

### Unit Testing with Embedded Kafka

**Maven Dependency:**
```xml
<dependency>
    <groupId>org.springframework.kafka</groupId>
    <artifactId>spring-kafka-test</artifactId>
    <version>3.0.0</version>
    <scope>test</scope>
</dependency>
```

**Test Example:**
```java
import org.springframework.kafka.test.EmbeddedKafkaBroker;
import org.junit.jupiter.api.*;

public class KafkaProducerTest {
    private EmbeddedKafkaBroker broker;
    
    @BeforeEach
    public void setup() {
        broker = new EmbeddedKafkaBroker(1);
        broker.afterPropertiesSet();
    }
    
    @AfterEach
    public void teardown() {
        broker.destroy();
    }
    
    @Test
    public void testProducer() {
        String brokerList = broker.getBrokersAsString();
        // Create producer with brokerList
        // Send test messages
        // Verify
    }
}
```

### Integration Testing

**Docker Compose for Tests:**
```yaml
# docker-compose.test.yml
version: '3.8'
services:
  kafka-test:
    image: confluentinc/cp-kafka:7.5.0
    ports:
      - "9092:9092"
    environment:
      KAFKA_ZOOKEEPER_CONNECT: zookeeper-test:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
  
  zookeeper-test:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
```

**Run Integration Tests:**
```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run tests
mvn integration-test

# Cleanup
docker-compose -f docker-compose.test.yml down -v
```

### Performance Testing

**Load Test Your Application:**
```bash
# Use the cluster's built-in perf tools
docker exec kafka-1 kafka-producer-perf-test \
  --topic test-topic \
  --num-records 100000 \
  --record-size 1024 \
  --throughput 10000 \
  --producer-props bootstrap.servers=kafka-1:19092
```

---

## Troubleshooting

### Connection Issues

**Problem:** Can't connect to Kafka

**Check:**
```bash
# 1. Verify brokers are running
docker-compose ps

# 2. Test network connectivity
telnet localhost 9092

# 3. Check bootstrap.servers configuration
# From host: localhost:9092
# From Docker: kafka-1:19092
# From external: <EXTERNAL_IP>:9092
```

### Message Not Received

**Checklist:**
- [ ] Topic exists: `kafka-topics --list`
- [ ] Consumer subscribed to correct topic
- [ ] Consumer in correct group
- [ ] Check offset: might be reading from latest when messages were sent earlier
- [ ] Check consumer lag: `kafka-consumer-groups --describe --group X`

**Reset Offset to Read All:**
```bash
docker exec kafka-1 kafka-consumer-groups \
  --bootstrap-server kafka-1:19092 \
  --group my-group \
  --topic my-topic \
  --reset-offsets --to-earliest \
  --execute
```

### High Latency

**Symptoms:** Producer P99 latency > 500ms

**Solutions:**
```java
// Increase timeouts
props.put("request.timeout.ms", "60000");
props.put("delivery.timeout.ms", "180000");

// Reduce batching
props.put("linger.ms", "0");
props.put("batch.size", "0");

// Check broker health
// Check network between client and brokers
```

### Out of Memory

**Symptoms:** `OutOfMemoryError` in application

**Check:**
```java
// Don't accumulate records
List<ProducerRecord> records = new ArrayList<>();
for (int i = 0; i < 1000000; i++) {
    records.add(new ProducerRecord<>("topic", "key", "value"));  // BAD - OOM!
}

// Send immediately instead
for (int i = 0; i < 1000000; i++) {
    producer.send(new ProducerRecord<>("topic", "key", "value"));  // GOOD
}
```

### Duplicate Messages

**Cause:** At-least-once delivery semantics

**Solutions:**
1. **Enable idempotence:**
   ```java
   props.put("enable.idempotence", "true");
   ```

2. **Use transactions:**
   ```java
   props.put("transactional.id", "my-tx-id");
   ```

3. **Implement idempotent processing:**
   ```java
   // Track processed message IDs
   Set<String> processedIds = new HashSet<>();
   
   for (ConsumerRecord<String, String> record : records) {
       String messageId = extractMessageId(record);
       if (!processedIds.contains(messageId)) {
           processRecord(record);
           processedIds.add(messageId);
       }
   }
   ```

---

## Code Examples

### Python Producer

```python
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092', 'localhost:9093', 'localhost:9094'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    acks='all',
    retries=3,
    compression_type='lz4'
)

# Send message
future = producer.send('my-topic', {'key': 'value'})

# Wait for confirmation
try:
    record_metadata = future.get(timeout=10)
    print(f"Sent to partition {record_metadata.partition} offset {record_metadata.offset}")
except Exception as e:
    print(f"Failed: {e}")

producer.close()
```

### Python Consumer

```python
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'my-topic',
    bootstrap_servers=['localhost:9092', 'localhost:9093', 'localhost:9094'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    group_id='my-python-group',
    auto_offset_reset='earliest',
    enable_auto_commit=False
)

for message in consumer:
    print(f"Received: {message.value}")
    # Process message
    consumer.commit()

consumer.close()
```

### Node.js Producer (KafkaJS)

```javascript
const { Kafka } = require('kafkajs');

const kafka = new Kafka({
  clientId: 'my-app',
  brokers: ['localhost:9092', 'localhost:9093', 'localhost:9094']
});

const producer = kafka.producer();

async function produce() {
  await producer.connect();
  
  await producer.send({
    topic: 'my-topic',
    messages: [
      { key: 'key1', value: 'hello world' }
    ],
    acks: -1,
    compression: 1  // GZIP
  });
  
  await producer.disconnect();
}

produce().catch(console.error);
```

### Node.js Consumer (KafkaJS)

```javascript
const { Kafka } = require('kafkajs');

const kafka = new Kafka({
  clientId: 'my-app',
  brokers: ['localhost:9092', 'localhost:9093', 'localhost:9094']
});

const consumer = kafka.consumer({ groupId: 'my-node-group' });

async function consume() {
  await consumer.connect();
  await consumer.subscribe({ topic: 'my-topic', fromBeginning: true });
  
  await consumer.run({
    eachMessage: async ({ topic, partition, message }) => {
      console.log({
        value: message.value.toString(),
        partition: partition,
        offset: message.offset
      });
    }
  });
}

consume().catch(console.error);
```

### Go Producer

```go
package main

import (
    "context"
    "fmt"
    "github.com/segmentio/kafka-go"
)

func main() {
    writer := kafka.NewWriter(kafka.WriterConfig{
        Brokers:  []string{"localhost:9092", "localhost:9093", "localhost:9094"},
        Topic:    "my-topic",
        Balancer: &kafka.LeastBytes{},
    })

    err := writer.WriteMessages(context.Background(),
        kafka.Message{
            Key:   []byte("key1"),
            Value: []byte("hello world"),
        },
    )
    if err != nil {
        panic(err)
    }

    writer.Close()
}
```

### Go Consumer

```go
package main

import (
    "context"
    "fmt"
    "github.com/segmentio/kafka-go"
)

func main() {
    reader := kafka.NewReader(kafka.ReaderConfig{
        Brokers:  []string{"localhost:9092", "localhost:9093", "localhost:9094"},
        Topic:    "my-topic",
        GroupID:  "my-go-group",
        MinBytes: 1,
        MaxBytes: 10e6,
    })

    for {
        msg, err := reader.ReadMessage(context.Background())
        if err != nil {
            break
        }
        fmt.Printf("Received: %s\n", string(msg.Value))
    }

    reader.Close()
}
```

---

## Reference

### Maven Dependencies

```xml
<dependencies>
    <!-- Kafka Clients -->
    <dependency>
        <groupId>org.apache.kafka</groupId>
        <artifactId>kafka-clients</artifactId>
        <version>3.5.0</version>
    </dependency>
    
    <!-- Logging -->
    <dependency>
        <groupId>org.slf4j</groupId>
        <artifactId>slf4j-api</artifactId>
        <version>2.0.7</version>
    </dependency>
    
    <!-- Testing -->
    <dependency>
        <groupId>org.springframework.kafka</groupId>
        <artifactId>spring-kafka-test</artifactId>
        <version>3.0.0</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```

### Gradle Dependencies

```gradle
dependencies {
    implementation 'org.apache.kafka:kafka-clients:3.5.0'
    implementation 'org.slf4j:slf4j-api:2.0.7'
    testImplementation 'org.springframework.kafka:spring-kafka-test:3.0.0'
}
```

### Useful Links

- **Apache Kafka Documentation:** https://kafka.apache.org/documentation/
- **Kafka Clients:** https://kafka.apache.org/documentation/#api
- **KafkaJS (Node.js):** https://kafka.js.org/
- **kafka-python:** https://kafka-python.readthedocs.io/
- **Confluent Platform:** https://docs.confluent.io/

---

**Developer Guide Version:** 2.0  
**Last Updated:** 2025-10-30  
**Next Review:** Quarterly or after major Kafka version upgrade
