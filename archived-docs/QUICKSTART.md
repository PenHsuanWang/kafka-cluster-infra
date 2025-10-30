# Quick Start Guide

## Prerequisites
- Docker 20.10+ and Docker Compose 2.0+
- Minimum 24GB RAM (for 3 brokers with 8GB heap each)
- Minimum 100GB disk space

## Start the Cluster

```bash
# Option 1: Using the start script (recommended)
./scripts/start-cluster.sh

# Option 2: Using Make
make start

# Option 3: Using docker-compose directly
docker-compose up -d
```

## Verify the Cluster

```bash
# Check health
make health

# Or manually
docker-compose ps
```

## Create Topics

```bash
# Create example topics
make topics

# Or manually
./scripts/create-topics.sh
```

## Run Performance Test

```bash
make test
```

## Access Kafka UI

Open browser: http://localhost:8080

## Connect Your Application

### Bootstrap Servers (External Access)
```
localhost:9092,localhost:9093,localhost:9094
```

### Bootstrap Servers (Container-to-Container)
```
kafka-1:19092,kafka-2:19093,kafka-3:19094
```

## Producer Example (Python)

```python
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092', 'localhost:9093', 'localhost:9094'],
    acks='all',
    compression_type='lz4',
    linger_ms=100,
    batch_size=1048576
)

producer.send('my-topic', b'Hello Kafka!')
producer.flush()
```

## Consumer Example (Python)

```python
from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'my-topic',
    bootstrap_servers=['localhost:9092', 'localhost:9093', 'localhost:9094'],
    group_id='my-consumer-group',
    auto_offset_reset='earliest'
)

for message in consumer:
    print(f"Received: {message.value}")
```

## Stop the Cluster

```bash
# Graceful stop
make stop

# Or
./scripts/stop-cluster.sh

# Or
docker-compose down
```

## Useful Commands

```bash
make help           # Show all available commands
make status         # Show cluster status
make logs           # View all logs
make logs-kafka     # View Kafka logs only
make shell-kafka    # Open shell in Kafka broker
make clean          # Remove everything (DATA LOSS!)
```

## Troubleshooting

### Cluster not starting?
1. Check memory: `free -h`
2. Check disk space: `df -h`
3. Check logs: `docker-compose logs`

### Performance issues?
1. Adjust heap size in `.env`
2. Check resource usage: `docker stats`
3. Review configuration tuning in README.md

For detailed documentation, see [README.md](README.md)
