"""
Multi-threaded Kafka consumer for stress testing
"""

import time, json, threading, os
from datetime import datetime
from confluent_kafka import Consumer, KafkaError
import config


class StressConsumer:
    def __init__(self, consumer_id, group_id, timeout_seconds=60):
        self.consumer_id = consumer_id
        self.group_id = group_id
        self.timeout_seconds = timeout_seconds
        self.stats = {
            'consumed': 0, 
            'errors': 0, 
            'latencies': [],  # End-to-end latency (t3 - t1)
            'kafka_to_consumer_times': [],  # t3 - t2: time from kafka ack to consumer receive
            'start_time': None, 
            'end_time': None, 
            'error_messages': []
        }
        
        self.consumer = Consumer({
            'bootstrap.servers': ','.join(config.KAFKA_BROKERS),
            'group.id': group_id,
            'auto.offset.reset': config.CONSUMER_AUTO_OFFSET_RESET,
            'enable.auto.commit': config.CONSUMER_ENABLE_AUTO_COMMIT,
            'auto.commit.interval.ms': config.CONSUMER_AUTO_COMMIT_INTERVAL_MS,
            'max.poll.interval.ms': 300000,
            'session.timeout.ms': 30000,
        })
        self.consumer.subscribe([config.TEST_TOPIC])
        self.running = True
    
    def calculate_end_to_end_latency(self, message_timestamp):
        try:
            msg_time = datetime.fromisoformat(message_timestamp)
            return (datetime.utcnow() - msg_time).total_seconds() * 1000
        except:
            return None
    
    def calculate_kafka_to_consumer_latency(self, t2_ack_time):
        """Calculate time from Kafka acknowledgment (t2) to consumer receive (t3)"""
        try:
            t3 = time.time()
            return (t3 - t2_ack_time) * 1000  # Convert to ms
        except:
            return None
    
    def run(self):
        print(f"Consumer {self.consumer_id} (Group: {self.group_id}): Starting...")
        self.stats['start_time'] = time.time()
        start_time = time.time()
        consecutive_empty_polls = 0
        
        try:
            while self.running:
                if time.time() - start_time > self.timeout_seconds:
                    print(f"Consumer {self.consumer_id}: Timeout reached")
                    break
                
                msg = self.consumer.poll(timeout=1.0)
                
                if msg is None:
                    consecutive_empty_polls += 1
                    if consecutive_empty_polls >= 10:
                        print(f"Consumer {self.consumer_id}: No more messages")
                        break
                    continue
                
                consecutive_empty_polls = 0
                
                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        self.stats['errors'] += 1
                        self.stats['error_messages'].append(str(msg.error()))
                    continue
                
                try:
                    t3 = time.time()  # Time when consumer receives the message
                    message_data = json.loads(msg.value().decode('utf-8'))
                    
                    # Calculate end-to-end latency (t3 - t1)
                    if 'timestamp' in message_data:
                        latency = self.calculate_end_to_end_latency(message_data['timestamp'])
                        if latency is not None:
                            self.stats['latencies'].append(latency)
                    
                    # Calculate kafka-to-consumer latency (t3 - t2)
                    if 't2' in message_data or 't1_send_time' in message_data:
                        # If t2 is available, use it; otherwise approximate with t1
                        t2 = message_data.get('t2', message_data.get('t1_send_time'))
                        if t2:
                            kafka_to_consumer_time = (t3 - t2) * 1000  # Convert to ms
                            self.stats['kafka_to_consumer_times'].append({
                                't2': t2,
                                't3': t3,
                                'duration_ms': kafka_to_consumer_time
                            })
                    
                    self.stats['consumed'] += 1
                except Exception as e:
                    self.stats['errors'] += 1
                    self.stats['error_messages'].append(f"Parse error: {str(e)}")
        
        except Exception as e:
            self.stats['errors'] += 1
            self.stats['error_messages'].append(f"Consumer error: {str(e)}")
        finally:
            self.consumer.close()
            self.stats['end_time'] = time.time()
        
        print(f"Consumer {self.consumer_id}: Consumed: {self.stats['consumed']}, Errors: {self.stats['errors']}")
        return self.stats


class MultiConsumerStressTest:
    def __init__(self):
        self.consumers, self.results = [], []
    
    def run_test(self, timeout_seconds=120):
        print(f"\n{'='*60}\nStarting Multi-Consumer Stress Test\n{'='*60}")
        print(f"Groups: {config.NUM_CONSUMER_GROUPS}, Consumers/Group: {config.CONSUMERS_PER_GROUP}")
        print(f"Total: {config.NUM_CONSUMER_GROUPS * config.CONSUMERS_PER_GROUP}, Timeout: {timeout_seconds}s\n")
        
        start_time = time.time()
        threads = []
        consumer_id = 0
        
        for group_idx in range(config.NUM_CONSUMER_GROUPS):
            group_id = f"stress-test-group-{group_idx}"
            for consumer_idx in range(config.CONSUMERS_PER_GROUP):
                consumer = StressConsumer(consumer_id, group_id, timeout_seconds)
                self.consumers.append(consumer)
                thread = threading.Thread(target=lambda c: self.results.append(c.run()), args=(consumer,))
                threads.append(thread)
                thread.start()
                consumer_id += 1
                time.sleep(0.05)
        
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        print(f"\n{'='*60}\nCompleted in {end_time - start_time:.2f}s\n{'='*60}\n")
        return self.aggregate_results(start_time, end_time)
    
    def aggregate_results(self, start_time, end_time):
        total_consumed = sum(r['consumed'] for r in self.results)
        total_errors = sum(r['errors'] for r in self.results)
        all_latencies = [l for r in self.results for l in r['latencies']]
        
        # Collect all kafka_to_consumer timing data
        all_kafka_to_consumer = []
        for r in self.results:
            all_kafka_to_consumer.extend(r.get('kafka_to_consumer_times', []))
        
        duration = end_time - start_time
        throughput_msgs = total_consumed / duration if duration > 0 else 0
        throughput_mb = (total_consumed * config.MESSAGE_SIZE_BYTES) / (1024 * 1024 * duration) if duration > 0 else 0
        
        # Calculate kafka_to_consumer statistics
        kafka_to_consumer_durations = [item['duration_ms'] for item in all_kafka_to_consumer]
        
        return {
            'test_type': 'consumer',
            'start_time': datetime.fromtimestamp(start_time).isoformat(),
            'end_time': datetime.fromtimestamp(end_time).isoformat(),
            'duration_seconds': duration,
            'num_consumer_groups': config.NUM_CONSUMER_GROUPS,
            'consumers_per_group': config.CONSUMERS_PER_GROUP,
            'total_consumers': config.NUM_CONSUMER_GROUPS * config.CONSUMERS_PER_GROUP,
            'total_messages_consumed': total_consumed,
            'total_errors': total_errors,
            'success_rate': total_consumed / (total_consumed + total_errors) if (total_consumed + total_errors) > 0 else 0,
            'throughput_msgs_per_sec': throughput_msgs,
            'throughput_mb_per_sec': throughput_mb,
            'latencies': all_latencies,
            'avg_end_to_end_latency_ms': sum(all_latencies) / len(all_latencies) if all_latencies else 0,
            'min_latency_ms': min(all_latencies) if all_latencies else 0,
            'max_latency_ms': max(all_latencies) if all_latencies else 0,
            'p50_latency_ms': self.percentile(all_latencies, 50),
            'p95_latency_ms': self.percentile(all_latencies, 95),
            'p99_latency_ms': self.percentile(all_latencies, 99),
            # New timing data for visualization
            'kafka_to_consumer_times': all_kafka_to_consumer,
            'avg_kafka_to_consumer_ms': sum(kafka_to_consumer_durations) / len(kafka_to_consumer_durations) if kafka_to_consumer_durations else 0,
            'p50_kafka_to_consumer_ms': self.percentile(kafka_to_consumer_durations, 50),
            'p95_kafka_to_consumer_ms': self.percentile(kafka_to_consumer_durations, 95),
            'p99_kafka_to_consumer_ms': self.percentile(kafka_to_consumer_durations, 99),
            'individual_consumer_stats': self.results
        }
    
    @staticmethod
    def percentile(data, percentile):
        if not data: return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


if __name__ == '__main__':
    test = MultiConsumerStressTest()
    results = test.run_test(timeout_seconds=120)
    
    os.makedirs(config.REPORT_OUTPUT_DIR, exist_ok=True)
    with open(f'{config.REPORT_OUTPUT_DIR}/consumer_results.json', 'w') as f:
        results_copy = results.copy()
        results_copy['latencies'] = f"[{len(results['latencies'])} measurements]"
        results_copy['kafka_to_consumer_times'] = f"[{len(results.get('kafka_to_consumer_times', []))} measurements]"
        results_copy['individual_consumer_stats'] = [{k: v if k not in ['latencies', 'kafka_to_consumer_times'] else f"[{len(v)} measurements]" for k, v in s.items()} for s in results['individual_consumer_stats']]
        json.dump(results_copy, f, indent=2)
    
    # Save detailed timing data for visualization
    with open(f'{config.REPORT_OUTPUT_DIR}/consumer_timing_data.json', 'w') as f:
        timing_data = {
            'kafka_to_consumer_times': results.get('kafka_to_consumer_times', []),
            'throughput_msgs_per_sec': results['throughput_msgs_per_sec'],
            'throughput_mb_per_sec': results['throughput_mb_per_sec']
        }
        json.dump(timing_data, f, indent=2)
    
    print("\n" + "="*60 + "\nCONSUMER STRESS TEST RESULTS\n" + "="*60)
    print(f"Messages consumed: {results['total_messages_consumed']:,}, Errors: {results['total_errors']:,}")
    print(f"Success rate: {results['success_rate']*100:.2f}%, Duration: {results['duration_seconds']:.2f}s")
    print(f"Throughput: {results['throughput_msgs_per_sec']:.2f} msgs/s, {results['throughput_mb_per_sec']:.2f} MB/s")
    print(f"\nEnd-to-End Latency: Avg={results['avg_end_to_end_latency_ms']:.2f}ms, P50={results['p50_latency_ms']:.2f}ms, P95={results['p95_latency_ms']:.2f}ms, P99={results['p99_latency_ms']:.2f}ms")
    print(f"\nKafka-to-Consumer (t3-t2): Avg={results['avg_kafka_to_consumer_ms']:.2f}ms, P50={results['p50_kafka_to_consumer_ms']:.2f}ms, P95={results['p95_kafka_to_consumer_ms']:.2f}ms, P99={results['p99_kafka_to_consumer_ms']:.2f}ms")
    print("="*60)
