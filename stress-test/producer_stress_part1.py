"""
Multi-threaded Kafka producer for stress testing
"""

import time
import json
import threading
import random
import string
from datetime import datetime
from collections import defaultdict
from confluent_kafka import Producer
from tqdm import tqdm
import config


class StressProducer:
    def __init__(self, producer_id, num_messages, message_size):
        self.producer_id = producer_id
        self.num_messages = num_messages
        self.message_size = message_size
        self.stats = {
            'sent': 0,
            'failed': 0,
            'latencies': [],
            'start_time': None,
            'end_time': None,
            'errors': []
        }
        
        self.producer = Producer({
            'bootstrap.servers': ','.join(config.KAFKA_BROKERS),
            'compression.type': config.PRODUCER_COMPRESSION_TYPE,
            'linger.ms': config.PRODUCER_LINGER_MS,
            'batch.size': config.PRODUCER_BATCH_SIZE,
            'acks': config.PRODUCER_ACKS,
            'max.in.flight.requests.per.connection': 5,
            'enable.idempotence': True,
        })
    
    def generate_message(self, msg_id):
        """Generate a random message of specified size"""
        payload_size = self.message_size - 200
        payload = ''.join(random.choices(string.ascii_letters + string.digits, k=max(1, payload_size)))
        
        message = {
            'producer_id': self.producer_id,
            'message_id': msg_id,
            'timestamp': datetime.utcnow().isoformat(),
            'payload': payload
        }
        return json.dumps(message).encode('utf-8')
    
    def delivery_callback(self, err, msg):
        """Callback for message delivery reports"""
        if err:
            self.stats['failed'] += 1
            self.stats['errors'].append(str(err))
        else:
            self.stats['sent'] += 1
