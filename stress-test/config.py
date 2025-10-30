"""
Configuration file for Kafka stress testing
"""

# Kafka cluster configuration
KAFKA_BROKERS = [
    'localhost:9092',
    'localhost:9093',
    'localhost:9094'
]

# Test configuration
TEST_TOPIC = 'stress-test-topic'
TEST_DURATION_SECONDS = 300  # 5 minutes

# Producer configuration
NUM_PRODUCERS = 10
MESSAGES_PER_PRODUCER = 10000
MESSAGE_SIZE_BYTES = 1024  # 1KB messages
PRODUCER_BATCH_SIZE = 16384
PRODUCER_LINGER_MS = 10
PRODUCER_COMPRESSION_TYPE = 'lz4'
PRODUCER_ACKS = 'all'

# Consumer configuration
NUM_CONSUMER_GROUPS = 5
CONSUMERS_PER_GROUP = 3
CONSUMER_AUTO_OFFSET_RESET = 'earliest'
CONSUMER_ENABLE_AUTO_COMMIT = True
CONSUMER_AUTO_COMMIT_INTERVAL_MS = 1000

# Topic configuration
TOPIC_PARTITIONS = 12
TOPIC_REPLICATION_FACTOR = 3
TOPIC_MIN_ISR = 2

# Performance thresholds
MAX_ACCEPTABLE_LATENCY_MS = 100
MIN_ACCEPTABLE_THROUGHPUT_MBPS = 5
MAX_ACCEPTABLE_ERROR_RATE = 0.01  # 1%

# Report configuration
REPORT_OUTPUT_DIR = 'test-results'
GENERATE_CHARTS = True
