"""
Multi-threaded Kafka producer for stress testing
"""

import time, json, threading, random, string, os
from datetime import datetime
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
            'latencies': [],  # t2 - t1: time from send to kafka ack
            'send_to_ack_times': [],  # Detailed timing: (t1, t2, t2-t1)
            'start_time': None, 
            'end_time': None, 
            'errors': []
        }
        # Track pending messages for callback timing
        self.pending_messages = {}
        self.lock = threading.Lock()
        
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
        payload_size = self.message_size - 200
        payload = ''.join(random.choices(string.ascii_letters + string.digits, k=max(1, payload_size)))
        # Use timestamp with microsecond precision for accurate timing
        t1 = time.time()
        message = {
            'producer_id': self.producer_id, 
            'message_id': msg_id, 
            'timestamp': datetime.utcnow().isoformat(),
            't1_send_time': t1,  # Time when message is sent
            'payload': payload
        }
        return json.dumps(message).encode('utf-8'), t1
    
    def delivery_callback(self, err, msg):
        if err:
            self.stats['failed'] += 1
            self.stats['errors'].append(str(err))
        else:
            t2 = time.time()  # Time when kafka acknowledges
            self.stats['sent'] += 1
            
            # Extract t1 from message to calculate t2 - t1
            try:
                msg_data = json.loads(msg.value().decode('utf-8'))
                t1 = msg_data.get('t1_send_time')
                if t1:
                    send_to_ack_time = (t2 - t1) * 1000  # Convert to ms
                    with self.lock:
                        self.stats['send_to_ack_times'].append({
                            't1': t1,
                            't2': t2,
                            'duration_ms': send_to_ack_time
                        })
            except Exception:
                pass
    
    def run(self):
        print(f"Producer {self.producer_id}: Starting {self.num_messages} messages...")
        self.stats['start_time'] = time.time()
        
        for i in tqdm(range(self.num_messages), desc=f"Producer {self.producer_id}", position=self.producer_id):
            try:
                message, t1 = self.generate_message(i)
                self.producer.produce(topic=config.TEST_TOPIC, value=message, callback=self.delivery_callback)
                self.producer.poll(0)
                msg_end = time.time()
                # Track latency for backward compatibility
                self.stats['latencies'].append((msg_end - t1) * 1000)
            except Exception as e:
                self.stats['failed'] += 1
                self.stats['errors'].append(str(e))
        
        self.producer.flush()
        self.stats['end_time'] = time.time()
        print(f"Producer {self.producer_id}: Sent: {self.stats['sent']}, Failed: {self.stats['failed']}")
        return self.stats


class MultiProducerStressTest:
    def __init__(self):
        self.producers, self.results = [], []
    
    def run_test(self):
        print(f"\n{'='*60}\nStarting Multi-Producer Stress Test\n{'='*60}")
        print(f"Producers: {config.NUM_PRODUCERS}, Messages/Producer: {config.MESSAGES_PER_PRODUCER}")
        print(f"Message Size: {config.MESSAGE_SIZE_BYTES}B, Total: {config.NUM_PRODUCERS * config.MESSAGES_PER_PRODUCER}\n")
        
        start_time = time.time()
        threads = []
        
        for i in range(config.NUM_PRODUCERS):
            producer = StressProducer(i, config.MESSAGES_PER_PRODUCER, config.MESSAGE_SIZE_BYTES)
            self.producers.append(producer)
            thread = threading.Thread(target=lambda p: self.results.append(p.run()), args=(producer,))
            threads.append(thread)
            thread.start()
            time.sleep(0.1)
        
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        print(f"\n{'='*60}\nCompleted in {end_time - start_time:.2f}s\n{'='*60}\n")
        return self.aggregate_results(start_time, end_time)
    
    def aggregate_results(self, start_time, end_time):
        total_sent = sum(r['sent'] for r in self.results)
        total_failed = sum(r['failed'] for r in self.results)
        all_latencies = [l for r in self.results for l in r['latencies']]
        
        # Collect all send_to_ack timing data
        all_send_to_ack = []
        for r in self.results:
            all_send_to_ack.extend(r.get('send_to_ack_times', []))
        
        duration = end_time - start_time
        throughput_msgs = total_sent / duration
        throughput_mb = (total_sent * config.MESSAGE_SIZE_BYTES) / (1024 * 1024 * duration)
        
        # Calculate send_to_ack statistics
        send_to_ack_durations = [item['duration_ms'] for item in all_send_to_ack]
        
        return {
            'test_type': 'producer',
            'start_time': datetime.fromtimestamp(start_time).isoformat(),
            'end_time': datetime.fromtimestamp(end_time).isoformat(),
            'duration_seconds': duration,
            'num_producers': config.NUM_PRODUCERS,
            'total_messages_sent': total_sent,
            'total_messages_failed': total_failed,
            'success_rate': total_sent / (total_sent + total_failed) if (total_sent + total_failed) > 0 else 0,
            'throughput_msgs_per_sec': throughput_msgs,
            'throughput_mb_per_sec': throughput_mb,
            'latencies': all_latencies,
            'avg_latency_ms': sum(all_latencies) / len(all_latencies) if all_latencies else 0,
            'min_latency_ms': min(all_latencies) if all_latencies else 0,
            'max_latency_ms': max(all_latencies) if all_latencies else 0,
            'p50_latency_ms': self.percentile(all_latencies, 50),
            'p95_latency_ms': self.percentile(all_latencies, 95),
            'p99_latency_ms': self.percentile(all_latencies, 99),
            # New timing data for visualization
            'send_to_ack_times': all_send_to_ack,
            'avg_send_to_ack_ms': sum(send_to_ack_durations) / len(send_to_ack_durations) if send_to_ack_durations else 0,
            'p50_send_to_ack_ms': self.percentile(send_to_ack_durations, 50),
            'p95_send_to_ack_ms': self.percentile(send_to_ack_durations, 95),
            'p99_send_to_ack_ms': self.percentile(send_to_ack_durations, 99),
            'individual_producer_stats': self.results
        }
    
    @staticmethod
    def percentile(data, percentile):
        if not data: return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


if __name__ == '__main__':
    test = MultiProducerStressTest()
    results = test.run_test()
    
    os.makedirs(config.REPORT_OUTPUT_DIR, exist_ok=True)
    with open(f'{config.REPORT_OUTPUT_DIR}/producer_results.json', 'w') as f:
        results_copy = results.copy()
        results_copy['latencies'] = f"[{len(results['latencies'])} measurements]"
        # Summarize send_to_ack_times for JSON output
        results_copy['send_to_ack_times'] = f"[{len(results.get('send_to_ack_times', []))} measurements]"
        results_copy['individual_producer_stats'] = [{k: v if k not in ['latencies', 'send_to_ack_times'] else f"[{len(v)} measurements]" for k, v in s.items()} for s in results['individual_producer_stats']]
        json.dump(results_copy, f, indent=2)
    
    # Save detailed timing data for visualization
    with open(f'{config.REPORT_OUTPUT_DIR}/producer_timing_data.json', 'w') as f:
        timing_data = {
            'send_to_ack_times': results.get('send_to_ack_times', []),
            'throughput_msgs_per_sec': results['throughput_msgs_per_sec'],
            'throughput_mb_per_sec': results['throughput_mb_per_sec']
        }
        json.dump(timing_data, f, indent=2)
    
    print("\n" + "="*60 + "\nPRODUCER STRESS TEST RESULTS\n" + "="*60)
    print(f"Messages sent: {results['total_messages_sent']:,}, Failed: {results['total_messages_failed']:,}")
    print(f"Success rate: {results['success_rate']*100:.2f}%, Duration: {results['duration_seconds']:.2f}s")
    print(f"Throughput: {results['throughput_msgs_per_sec']:.2f} msgs/s, {results['throughput_mb_per_sec']:.2f} MB/s")
    print(f"\nLatency: Avg={results['avg_latency_ms']:.2f}ms, P50={results['p50_latency_ms']:.2f}ms, P95={results['p95_latency_ms']:.2f}ms, P99={results['p99_latency_ms']:.2f}ms")
    print(f"\nSend-to-Ack (t2-t1): Avg={results['avg_send_to_ack_ms']:.2f}ms, P50={results['p50_send_to_ack_ms']:.2f}ms, P95={results['p95_send_to_ack_ms']:.2f}ms, P99={results['p99_send_to_ack_ms']:.2f}ms")
    print("="*60)
