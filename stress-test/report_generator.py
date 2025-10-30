"""
Generate comprehensive performance report with visualizations
"""

import json, os
from datetime import datetime
import config

try:
    from visualization import StressTestVisualizer
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    print("Warning: Visualization module not available. Charts will not be generated.")

class PerformanceReportGenerator:
    def __init__(self, producer_file, consumer_file):
        self.producer = self.load(producer_file)
        self.consumer = self.load(consumer_file)
        self.output_dir = config.REPORT_OUTPUT_DIR
    
    def load(self, filename):
        try:
            with open(filename) as f:
                return json.load(f)
        except:
            return None
    
    def generate_report(self):
        r = []
        r.append("# Kafka Cluster Stress Test Report\n")
        r.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        r.append("---\n\n## Executive Summary\n\n")
        
        if self.producer:
            ps = self.producer.get('success_rate', 0) * 100
            pt = self.producer.get('throughput_mb_per_sec', 0)
            p99 = self.producer.get('p99_latency_ms', 0)
            status = "✅ PASSED" if ps >= 99 and p99 < config.MAX_ACCEPTABLE_LATENCY_MS else "⚠️ NEEDS ATTENTION"
            r.append(f"**Status:** {status}\n\n")
            r.append(f"- **Producer Success:** {ps:.2f}%\n")
            r.append(f"- **Producer Throughput:** {pt:.2f} MB/s\n")
            r.append(f"- **Producer P99 Latency:** {p99:.2f} ms\n")
        
        if self.consumer:
            cs = self.consumer.get('success_rate', 0) * 100
            ct = self.consumer.get('throughput_mb_per_sec', 0)
            cp99 = self.consumer.get('p99_latency_ms', 0)
            r.append(f"- **Consumer Success:** {cs:.2f}%\n")
            r.append(f"- **Consumer Throughput:** {ct:.2f} MB/s\n")
            r.append(f"- **End-to-End P99:** {cp99:.2f} ms\n")
        
        r.append("\n---\n\n## Performance Visualizations\n\n")
        r.append("Detailed timing analysis charts have been generated:\n\n")
        r.append("- `timing_breakdown.png` - Average latency at each stage (t2-t1 and t3-t2)\n")
        r.append("- `timing_vs_throughput.png` - Latency variation with message throughput\n")
        r.append("- `end_to_end_pipeline.png` - Complete pipeline timing breakdown\n")
        r.append("- `latency_distribution.png` - Distribution of latencies for both stages\n")
        r.append("- `throughput_comparison.png` - Producer vs Consumer throughput comparison\n")
        
        r.append("\n---\n\n## Configuration\n\n")
        r.append(f"- **Brokers:** {', '.join(config.KAFKA_BROKERS)}\n")
        r.append(f"- **Topic:** {config.TEST_TOPIC}, Partitions: {config.TOPIC_PARTITIONS}\n")
        r.append(f"- **Producers:** {config.NUM_PRODUCERS} × {config.MESSAGES_PER_PRODUCER} messages\n")
        r.append(f"- **Message Size:** {config.MESSAGE_SIZE_BYTES} bytes\n")
        r.append(f"- **Consumer Groups:** {config.NUM_CONSUMER_GROUPS} × {config.CONSUMERS_PER_GROUP} consumers\n")
        
        if self.producer:
            r.append("\n---\n\n## Producer Results\n\n")
            r.append(f"**Duration:** {self.producer.get('duration_seconds', 0):.2f}s\n\n")
            r.append(f"- Messages Sent: {self.producer.get('total_messages_sent', 0):,}\n")
            r.append(f"- Failed: {self.producer.get('total_messages_failed', 0):,}\n")
            r.append(f"- Success Rate: {self.producer.get('success_rate', 0)*100:.2f}%\n")
            r.append(f"- Throughput: {self.producer.get('throughput_msgs_per_sec', 0):.2f} msgs/s ({self.producer.get('throughput_mb_per_sec', 0):.2f} MB/s)\n\n")
            r.append("**Latency (ms):**\n")
            r.append(f"- Avg: {self.producer.get('avg_latency_ms', 0):.2f}, P50: {self.producer.get('p50_latency_ms', 0):.2f}\n")
            r.append(f"- P95: {self.producer.get('p95_latency_ms', 0):.2f}, P99: {self.producer.get('p99_latency_ms', 0):.2f}\n\n")
            r.append("**Producer→Kafka Timing (t2-t1):**\n")
            r.append(f"- Avg: {self.producer.get('avg_send_to_ack_ms', 0):.2f}, P50: {self.producer.get('p50_send_to_ack_ms', 0):.2f}\n")
            r.append(f"- P95: {self.producer.get('p95_send_to_ack_ms', 0):.2f}, P99: {self.producer.get('p99_send_to_ack_ms', 0):.2f}\n")
        
        if self.consumer:
            r.append("\n---\n\n## Consumer Results\n\n")
            r.append(f"**Duration:** {self.consumer.get('duration_seconds', 0):.2f}s\n\n")
            r.append(f"- Messages Consumed: {self.consumer.get('total_messages_consumed', 0):,}\n")
            r.append(f"- Errors: {self.consumer.get('total_errors', 0):,}\n")
            r.append(f"- Success Rate: {self.consumer.get('success_rate', 0)*100:.2f}%\n")
            r.append(f"- Throughput: {self.consumer.get('throughput_msgs_per_sec', 0):.2f} msgs/s ({self.consumer.get('throughput_mb_per_sec', 0):.2f} MB/s)\n\n")
            r.append("**End-to-End Latency (ms):**\n")
            r.append(f"- Avg: {self.consumer.get('avg_end_to_end_latency_ms', 0):.2f}, P50: {self.consumer.get('p50_latency_ms', 0):.2f}\n")
            r.append(f"- P95: {self.consumer.get('p95_latency_ms', 0):.2f}, P99: {self.consumer.get('p99_latency_ms', 0):.2f}\n\n")
            r.append("**Kafka→Consumer Timing (t3-t2):**\n")
            r.append(f"- Avg: {self.consumer.get('avg_kafka_to_consumer_ms', 0):.2f}, P50: {self.consumer.get('p50_kafka_to_consumer_ms', 0):.2f}\n")
            r.append(f"- P95: {self.consumer.get('p95_kafka_to_consumer_ms', 0):.2f}, P99: {self.consumer.get('p99_kafka_to_consumer_ms', 0):.2f}\n")
        
        r.append("\n---\n\n## Assessment\n\n")
        
        if self.producer:
            ps = self.producer.get('success_rate', 0) * 100
            pt = self.producer.get('throughput_mb_per_sec', 0)
            p99 = self.producer.get('p99_latency_ms', 0)
            r.append("✅ Producer success ≥99%\n" if ps >= 99 else f"❌ Producer success {ps:.2f}%\n")
            r.append(f"✅ Throughput ≥{config.MIN_ACCEPTABLE_THROUGHPUT_MBPS} MB/s\n" if pt >= config.MIN_ACCEPTABLE_THROUGHPUT_MBPS else f"⚠️ Throughput {pt:.2f} MB/s\n")
            r.append(f"✅ P99 latency <{config.MAX_ACCEPTABLE_LATENCY_MS}ms\n" if p99 < config.MAX_ACCEPTABLE_LATENCY_MS else f"⚠️ P99 latency {p99:.2f}ms\n")
        
        if self.consumer:
            cs = self.consumer.get('success_rate', 0) * 100
            r.append("✅ Consumer success ≥99%\n" if cs >= 99 else f"❌ Consumer success {cs:.2f}%\n")
        
        r.append("\n---\n\n## Conclusion\n\n")
        if self.producer and self.consumer:
            ps = self.producer.get('success_rate', 0) * 100
            cs = self.consumer.get('success_rate', 0) * 100
            if ps >= 99 and cs >= 99:
                r.append("Cluster shows **excellent performance** and is production-ready.\n")
            elif ps >= 95 and cs >= 95:
                r.append("Cluster shows **good performance** with minor optimization opportunities.\n")
            else:
                r.append("Cluster requires **performance tuning** before production.\n")
        
        return ''.join(r)
    
    def save(self):
        print("\n" + "="*60)
        print("Generating Performance Report")
        print("="*60 + "\n")
        
        # Generate visualizations if available
        if VISUALIZATION_AVAILABLE:
            print("Generating visualization charts...")
            visualizer = StressTestVisualizer(self.output_dir)
            visualizer.generate_all_charts()
            print()
        
        report = self.generate_report()
        os.makedirs(config.REPORT_OUTPUT_DIR, exist_ok=True)
        with open(f'{config.REPORT_OUTPUT_DIR}/STRESS_TEST_REPORT.md', 'w') as f:
            f.write(report)
        
        print(f"✓ Report: {config.REPORT_OUTPUT_DIR}/STRESS_TEST_REPORT.md")
        print("\n" + "="*60)
        print("Report Complete!")
        print("="*60)


if __name__ == '__main__':
    gen = PerformanceReportGenerator(
        f'{config.REPORT_OUTPUT_DIR}/producer_results.json',
        f'{config.REPORT_OUTPUT_DIR}/consumer_results.json'
    )
    gen.output_dir = config.REPORT_OUTPUT_DIR
    gen.save()
