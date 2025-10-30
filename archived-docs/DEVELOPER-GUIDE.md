# Developer Guide - Kafka Cluster Integration

> **Target Audience:** Software Engineers, Application Developers  
> **Last Updated:** 2025-10-30  
> **Version:** 1.0

## Table of Contents
1. [Quick Start for Developers](#quick-start-for-developers)
2. [Client Configuration](#client-configuration)
3. [Producer Patterns](#producer-patterns)
4. [Consumer Patterns](#consumer-patterns)
5. [Best Practices](#best-practices)
6. [Testing Strategies](#testing-strategies)
7. [Troubleshooting](#troubleshooting)
8. [Code Examples](#code-examples)

---

## Quick Start for Developers

### Connection Configuration

**From Host Machine (Development):**
```
Bootstrap Servers: localhost:9092,localhost:9093,localhost:9094
```

**From Docker Network (Containerized Apps):**
```
Bootstrap Servers: kafka-1:19092,kafka-2:19093,kafka-3:19094
```

**From External Network (Production):**
```
# Update advertised.listeners in docker-compose.yml to use external IPs
# Then use: <external-ip-1>:9092,<external-ip-2>:9093,<external-ip-3>:9094
```

### Verify Connectivity

```bash
# Test connection
telnet localhost 9092

# List topics
docker exec kafka-1 kafka-topics --list \
  --bootstrap-server localhost:9092

# Create test topic
docker exec kafka-1 kafka-topics --create \
  --topic test-dev \
  --partitions 6 \
  --replication-factor 3 \
  --bootstrap-server kafka-1:19092
```

---

## Client Configuration

### Recommended Producer Configuration

```properties
# Basic Configuration
bootstrap.servers=localhost:9092,localhost:9093,localhost:9094
client.id=my-producer-app
key.serializer=org.apache.kafka.common.serialization.StringSerializer
value.serializer=org.apache.kafka.common.serialization.StringSerializer

# Reliability (for critical data)
acks=all                              # Wait for all replicas
retries=2147483647                    # Retry indefinitely
max.in.flight.requests.per.connection=5
enable.idempotence=true               # Prevent duplicates

# Performance
compression.type=lz4                  # Fast compression
batch.size=16384                      # 16KB batches
linger.ms=10                          # Small delay for batching
buffer.memory=33554432                # 32MB buffer

# Timeouts
request.timeout.ms=30000              # 30 seconds
delivery.timeout.ms=120000            # 2 minutes
max.block.ms=60000                    # 1 minute
```

### Recommended Consumer Configuration

```properties
# Basic Configuration
bootstrap.servers=localhost:9092,localhost:9093,localhost:9094
group.id=my-consumer-group
client.id=my-consumer-app
key.deserializer=org.apache.kafka.common.serialization.StringDeserializer
value.deserializer=org.apache.kafka.common.serialization.StringDeserializer

# Reliability
enable.auto.commit=false              # Manual commit for at-least-once
auto.offset.reset=earliest            # Start from beginning if no offset
isolation.level=read_committed        # Read only committed messages

# Performance
fetch.min.bytes=1024                  # Wait for 1KB
fetch.max.wait.ms=500                 # Or 500ms timeout
max.poll.records=500                  # Process 500 records per poll
max.poll.interval.ms=300000           # 5 minutes max processing time

# Session Management
session.timeout.ms=10000              # 10 seconds
heartbeat.interval.ms=3000            # 3 seconds
```

---

## Producer Patterns

### 1. Fire-and-Forget (Fast, but risky)

**Use Case:** Non-critical data, metrics, logs

```java
import org.apache.kafka.clients.producer.*;
import java.util.Properties;

public class FireAndForgetProducer {
    public static void main(String[] args) {
        Properties props = new Properties();
        props.put("bootstrap.servers", "localhost:9092,localhost:9093,localhost:9094");
        props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        props.put("acks", "1");  // Leader acknowledgment only
        
        Producer<String, String> producer = new KafkaProducer<>(props);
        
        try {
            for (int i = 0; i < 100; i++) {
                ProducerRecord<String, String> record = 
                    new ProducerRecord<>("my-topic", "key-" + i, "value-" + i);
                producer.send(record);  // No callback
            }
        } finally {
            producer.close();
        }
    }
}
```

### 2. Asynchronous Send with Callback (Recommended)

**Use Case:** Balance between performance and reliability

```java
import org.apache.kafka.clients.producer.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class AsyncProducerWithCallback {
    private static final Logger logger = LoggerFactory.getLogger(AsyncProducerWithCallback.class);
    
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
                            logger.error("Error sending message " + index, exception);
                            // Handle error (retry, dead letter queue, etc.)
                        } else {
                            logger.info("Message {} sent to partition {} with offset {}",
                                index, metadata.partition(), metadata.offset());
                        }
                    }
                });
            }
        } finally {
            producer.close();
        }
    }
}
```

### 3. Synchronous Send (Slowest, most reliable)

**Use Case:** Critical data requiring confirmation

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
                    RecordMetadata metadata = producer.send(record).get();  // Block until complete
                    System.out.printf("Sent to partition %d with offset %d%n",
                        metadata.partition(), metadata.offset());
                } catch (ExecutionException e) {
                    System.err.println("Error sending message: " + e.getCause());
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

### 4. Transactional Producer (Exactly-once semantics)

**Use Case:** Financial transactions, critical business events

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
                System.out.println("Transaction committed successfully");
            } catch (Exception e) {
                producer.abortTransaction();
                System.err.println("Transaction aborted: " + e.getMessage());
            }
        } finally {
            producer.close();
        }
    }
}
```

---

## Consumer Patterns

### 1. Basic Consumer (Auto-commit)

**Use Case:** Simple applications, at-most-once processing

```java
import org.apache.kafka.clients.consumer.*;
import java.time.Duration;
import java.util.*;

public class BasicConsumer {
    public static void main(String[] args) {
        Properties props = new Properties();
        props.put("bootstrap.servers", "localhost:9092,localhost:9093,localhost:9094");
        props.put("group.id", "my-consumer-group");
        props.put("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
        props.put("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
        props.put("enable.auto.commit", "true");
        props.put("auto.commit.interval.ms", "1000");
        
        Consumer<String, String> consumer = new KafkaConsumer<>(props);
        consumer.subscribe(Arrays.asList("my-topic"));
        
        try {
            while (true) {
                ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
                
                for (ConsumerRecord<String, String> record : records) {
                    System.out.printf("Received: partition=%d, offset=%d, key=%s, value=%s%n",
                        record.partition(), record.offset(), record.key(), record.value());
                    
                    // Process record
                    processRecord(record);
                }
            }
        } finally {
            consumer.close();
        }
    }
    
    private static void processRecord(ConsumerRecord<String, String> record) {
        // Your processing logic here
    }
}
```

### 2. Manual Commit Consumer (At-least-once)

**Use Case:** Reliable processing with possible duplicates

```java
import org.apache.kafka.clients.consumer.*;
import java.time.Duration;
import java.util.*;

public class ManualCommitConsumer {
    public static void main(String[] args) {
        Properties props = new Properties();
        props.put("bootstrap.servers", "localhost:9092,localhost:9093,localhost:9094");
        props.put("group.id", "my-consumer-group");
        props.put("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
        props.put("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
        props.put("enable.auto.commit", "false");  // Manual commit
        
        Consumer<String, String> consumer = new KafkaConsumer<>(props);
        consumer.subscribe(Arrays.asList("my-topic"));
        
        try {
            while (true) {
                ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
                
                for (ConsumerRecord<String, String> record : records) {
                    try {
                        // Process record
                        processRecord(record);
                        
                        // Commit after successful processing
                        consumer.commitSync();
                    } catch (Exception e) {
                        System.err.println("Error processing record: " + e.getMessage());
                        // Don't commit on error - will reprocess on restart
                    }
                }
            }
        } finally {
            consumer.close();
        }
    }
    
    private static void processRecord(ConsumerRecord<String, String> record) {
        // Your processing logic here
        System.out.printf("Processing: %s%n", record.value());
    }
}
```

### 3. Batch Processing Consumer

**Use Case:** Bulk database inserts, batch analytics

```java
import org.apache.kafka.clients.consumer.*;
import java.time.Duration;
import java.util.*;

public class BatchConsumer {
    public static void main(String[] args) {
        Properties props = new Properties();
        props.put("bootstrap.servers", "localhost:9092,localhost:9093,localhost:9094");
        props.put("group.id", "batch-consumer-group");
        props.put("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
        props.put("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
        props.put("enable.auto.commit", "false");
        props.put("max.poll.records", "500");  // Larger batch size
        
        Consumer<String, String> consumer = new KafkaConsumer<>(props);
        consumer.subscribe(Arrays.asList("my-topic"));
        
        try {
            while (true) {
                ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(1000));
                
                if (!records.isEmpty()) {
                    List<String> batch = new ArrayList<>();
                    
                    for (ConsumerRecord<String, String> record : records) {
                        batch.add(record.value());
                    }
                    
                    try {
                        // Process entire batch
                        processBatch(batch);
                        
                        // Commit only after successful batch processing
                        consumer.commitSync();
                        System.out.printf("Processed batch of %d records%n", batch.size());
                    } catch (Exception e) {
                        System.err.println("Error processing batch: " + e.getMessage());
                        // Seek back to last committed offset
                        consumer.seek(null, 0);  // Simplified - implement proper seek logic
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

### 4. Multi-threaded Consumer

**Use Case:** High-throughput parallel processing

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
        
        // Each thread gets its own consumer
        for (int i = 0; i < NUM_THREADS; i++) {
            executor.submit(new ConsumerThread(props, i));
        }
        
        // Graceful shutdown hook
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.out.println("Shutting down consumers...");
            executor.shutdownNow();
        }));
    }
    
    static class ConsumerThread implements Runnable {
        private final Consumer<String, String> consumer;
        private final int threadId;
        
        public ConsumerThread(Properties props, int threadId) {
            this.threadId = threadId;
            this.consumer = new KafkaConsumer<>(props);
            consumer.subscribe(Arrays.asList("my-topic"));
        }
        
        @Override
        public void run() {
            try {
                while (true) {
                    ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
                    
                    for (ConsumerRecord<String, String> record : records) {
                        System.out.printf("Thread %d processing: %s%n", threadId, record.value());
                        processRecord(record);
                    }
                    
                    if (!records.isEmpty()) {
                        consumer.commitSync();
                    }
                }
            } catch (Exception e) {
                System.err.printf("Thread %d error: %s%n", threadId, e.getMessage());
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

```bash
# Good: Use meaningful, hierarchical naming
events.user.registration
events.order.created
metrics.app.performance

# Bad: Vague or flat naming
topic1
data
events

# Create topics with proper configuration
docker exec kafka-1 kafka-topics --create \
  --topic events.user.registration \
  --partitions 12 \
  --replication-factor 3 \
  --config min.insync.replicas=2 \
  --config compression.type=lz4 \
  --config retention.ms=604800000 \
  --bootstrap-server kafka-1:19092
```

### Partition Key Selection

```java
// Good: Consistent hashing for related messages
ProducerRecord<String, String> record = 
    new ProducerRecord<>("orders", customerId, orderData);

// Bad: Random keys (breaks ordering)
ProducerRecord<String, String> record = 
    new ProducerRecord<>("orders", UUID.randomUUID().toString(), orderData);

// Null key: Round-robin distribution (no ordering)
ProducerRecord<String, String> record = 
    new ProducerRecord<>("logs", null, logMessage);
```

### Error Handling

```java
// Implement retry with exponential backoff
int maxRetries = 3;
int baseDelay = 1000;  // 1 second

for (int retry = 0; retry < maxRetries; retry++) {
    try {
        producer.send(record).get();
        break;  // Success
    } catch (Exception e) {
        if (retry == maxRetries - 1) {
            // Send to dead letter queue
            sendToDeadLetterQueue(record, e);
        } else {
            long delay = baseDelay * (1L << retry);  // Exponential backoff
            Thread.sleep(delay);
        }
    }
}
```

### Resource Management

```java
// Use try-with-resources for auto-closing
try (Producer<String, String> producer = new KafkaProducer<>(props)) {
    producer.send(record);
} // Producer automatically closed

// Configure appropriate timeouts
props.put("request.timeout.ms", "30000");
props.put("max.block.ms", "60000");
props.put("delivery.timeout.ms", "120000");
```

---

## Testing Strategies

### Unit Testing with EmbeddedKafka

```java
import org.springframework.kafka.test.EmbeddedKafkaBroker;
import org.junit.jupiter.api.Test;

public class KafkaProducerTest {
    @Test
    public void testProducer() {
        EmbeddedKafkaBroker broker = new EmbeddedKafkaBroker(1);
        broker.afterPropertiesSet();
        
        try {
            // Your test code here
            String brokerList = broker.getBrokersAsString();
            // ... create producer with brokerList
            // ... send test messages
            // ... verify
        } finally {
            broker.destroy();
        }
    }
}
```

### Integration Testing

```bash
# Use docker-compose for integration tests
docker-compose -f docker-compose.test.yml up -d

# Run your integration tests
mvn integration-test

# Cleanup
docker-compose -f docker-compose.test.yml down -v
```

### Load Testing

```bash
# Use kafka-producer-perf-test
docker exec kafka-1 kafka-producer-perf-test \
  --topic test-topic \
  --num-records 100000 \
  --record-size 1024 \
  --throughput 10000 \
  --producer-props bootstrap.servers=kafka-1:19092
```

---

## Troubleshooting

### Common Issues

#### 1. Connection Refused

```bash
# Check if Kafka is running
docker-compose ps

# Check network connectivity
telnet localhost 9092

# Verify advertised.listeners configuration
docker exec kafka-1 cat /etc/kafka/server.properties | grep advertised
```

#### 2. Producer Timeout

```java
// Increase timeouts in producer config
props.put("request.timeout.ms", "60000");      // 60 seconds
props.put("max.block.ms", "120000");           // 2 minutes
props.put("delivery.timeout.ms", "180000");    // 3 minutes
```

#### 3. Consumer Lag

```bash
# Check consumer group lag
docker exec kafka-1 kafka-consumer-groups --describe \
  --bootstrap-server kafka-1:19092 \
  --group my-consumer-group

# Solutions:
# - Add more consumers to group
# - Increase max.poll.records
# - Optimize processing logic
# - Add more partitions to topic
```

#### 4. Message Loss Prevention

```java
// Producer: Use reliable configuration
props.put("acks", "all");
props.put("retries", Integer.MAX_VALUE);
props.put("enable.idempotence", "true");
props.put("max.in.flight.requests.per.connection", "5");

// Consumer: Manual commit after processing
props.put("enable.auto.commit", "false");
consumer.commitSync();  // Commit after processing
```

---

## Code Examples

### Python Producer Example

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
result = future.get(timeout=10)  # Block until sent

producer.close()
```

### Python Consumer Example

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

### Node.js Producer Example

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
    acks: -1,  // All replicas
    compression: 1  // GZIP
  });
  
  await producer.disconnect();
}

produce();
```

### Node.js Consumer Example

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

consume();
```

---

## Additional Resources

- **Kafka UI:** http://localhost:8080
- **JMX Monitoring:** See [JMX-ACCESS-GUIDE.md](JMX-ACCESS-GUIDE.md)
- **Performance Testing:** See [PERFORMANCE-TESTING-GUIDE.md](PERFORMANCE-TESTING-GUIDE.md)
- **Production Deployment:** See [PRODUCTION-CHECKLIST.md](PRODUCTION-CHECKLIST.md)

---

**Document Version:** 1.0  
**Last Review:** 2025-10-30  
**Next Review:** After major Kafka version upgrade
