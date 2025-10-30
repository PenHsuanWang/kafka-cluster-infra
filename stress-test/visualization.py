"""
Visualization module for Kafka stress test results
Generates comprehensive matplotlib charts for timing analysis
"""

import json
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime
import config


class StressTestVisualizer:
    """Generate visualization charts for Kafka stress test performance analysis"""
    
    def __init__(self, output_dir='test-results'):
        self.output_dir = output_dir
        self.producer_data = None
        self.consumer_data = None
        self.producer_timing = None
        self.consumer_timing = None
        
        # Set style for professional-looking charts
        plt.style.use('seaborn-v0_8-darkgrid')
        
    def load_data(self):
        """Load test results and timing data from JSON files"""
        try:
            # Load producer results
            with open(f'{self.output_dir}/producer_results.json', 'r') as f:
                self.producer_data = json.load(f)
            
            # Load consumer results
            with open(f'{self.output_dir}/consumer_results.json', 'r') as f:
                self.consumer_data = json.load(f)
            
            # Load detailed timing data
            with open(f'{self.output_dir}/producer_timing_data.json', 'r') as f:
                self.producer_timing = json.load(f)
            
            with open(f'{self.output_dir}/consumer_timing_data.json', 'r') as f:
                self.consumer_timing = json.load(f)
            
            return True
        except FileNotFoundError as e:
            print(f"Error loading data: {e}")
            return False
    
    def plot_timing_breakdown(self):
        """
        Plot timing breakdown showing:
        - Average time for Producer -> Kafka (t2 - t1)
        - Average time for Kafka -> Consumer (t3 - t2)
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Extract timing data
        send_to_ack_times = self.producer_timing.get('send_to_ack_times', [])
        kafka_to_consumer_times = self.consumer_timing.get('kafka_to_consumer_times', [])
        
        if not send_to_ack_times or not kafka_to_consumer_times:
            print("Warning: Insufficient timing data for visualization")
            return
        
        # Calculate statistics for Producer -> Kafka (t2 - t1)
        send_to_ack_durations = [item['duration_ms'] for item in send_to_ack_times]
        avg_send_to_ack = np.mean(send_to_ack_durations)
        p50_send_to_ack = np.percentile(send_to_ack_durations, 50)
        p95_send_to_ack = np.percentile(send_to_ack_durations, 95)
        p99_send_to_ack = np.percentile(send_to_ack_durations, 99)
        
        # Calculate statistics for Kafka -> Consumer (t3 - t2)
        kafka_to_consumer_durations = [item['duration_ms'] for item in kafka_to_consumer_times]
        avg_kafka_to_consumer = np.mean(kafka_to_consumer_durations)
        p50_kafka_to_consumer = np.percentile(kafka_to_consumer_durations, 50)
        p95_kafka_to_consumer = np.percentile(kafka_to_consumer_durations, 95)
        p99_kafka_to_consumer = np.percentile(kafka_to_consumer_durations, 99)
        
        # Plot 1: Producer -> Kafka timing breakdown
        metrics = ['Avg', 'P50', 'P95', 'P99']
        values = [avg_send_to_ack, p50_send_to_ack, p95_send_to_ack, p99_send_to_ack]
        colors = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c']
        
        bars1 = ax1.bar(metrics, values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
        ax1.set_ylabel('Time (ms)', fontsize=12, fontweight='bold')
        ax1.set_title('Producer → Kafka (t2 - t1)\nTime from Send to Acknowledgment', 
                     fontsize=14, fontweight='bold', pad=20)
        ax1.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bar, value in zip(bars1, values):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value:.2f}ms',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # Plot 2: Kafka -> Consumer timing breakdown
        values2 = [avg_kafka_to_consumer, p50_kafka_to_consumer, p95_kafka_to_consumer, p99_kafka_to_consumer]
        bars2 = ax2.bar(metrics, values2, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
        ax2.set_ylabel('Time (ms)', fontsize=12, fontweight='bold')
        ax2.set_title('Kafka → Consumer (t3 - t2)\nTime from Acknowledgment to Consumption', 
                     fontsize=14, fontweight='bold', pad=20)
        ax2.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bar, value in zip(bars2, values2):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value:.2f}ms',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        output_path = f'{self.output_dir}/timing_breakdown.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Generated: {output_path}")
    
    def plot_timing_vs_throughput(self):
        """
        Plot timing (t2-t1 and t3-t2) versus message throughput
        Shows how latency changes with throughput
        """
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Extract timing data
        send_to_ack_times = self.producer_timing.get('send_to_ack_times', [])
        kafka_to_consumer_times = self.consumer_timing.get('kafka_to_consumer_times', [])
        
        if not send_to_ack_times or not kafka_to_consumer_times:
            print("Warning: Insufficient timing data for throughput analysis")
            return
        
        # Calculate cumulative throughput over time for producer
        producer_throughput = self.producer_data.get('throughput_msgs_per_sec', 0)
        consumer_throughput = self.consumer_data.get('throughput_msgs_per_sec', 0)
        
        # Sample data points for visualization (to avoid overcrowding)
        sample_size = min(1000, len(send_to_ack_times))
        sample_indices_prod = np.linspace(0, len(send_to_ack_times)-1, sample_size, dtype=int)
        sample_indices_cons = np.linspace(0, len(kafka_to_consumer_times)-1, sample_size, dtype=int)
        
        # Extract sampled timing values
        sampled_send_to_ack = [send_to_ack_times[i]['duration_ms'] for i in sample_indices_prod]
        sampled_kafka_to_consumer = [kafka_to_consumer_times[i]['duration_ms'] for i in sample_indices_cons]
        
        # Create message sequence numbers for x-axis
        message_nums_prod = np.linspace(0, len(send_to_ack_times), sample_size)
        message_nums_cons = np.linspace(0, len(kafka_to_consumer_times), sample_size)
        
        # Plot both timing metrics
        ax.scatter(message_nums_prod, sampled_send_to_ack, 
                  alpha=0.5, s=20, c='#3498db', label='Producer→Kafka (t2-t1)', marker='o')
        ax.scatter(message_nums_cons, sampled_kafka_to_consumer, 
                  alpha=0.5, s=20, c='#e74c3c', label='Kafka→Consumer (t3-t2)', marker='^')
        
        # Add trend lines
        z_prod = np.polyfit(message_nums_prod, sampled_send_to_ack, 2)
        p_prod = np.poly1d(z_prod)
        ax.plot(message_nums_prod, p_prod(message_nums_prod), 
               color='#2980b9', linewidth=2, linestyle='--', alpha=0.8)
        
        z_cons = np.polyfit(message_nums_cons, sampled_kafka_to_consumer, 2)
        p_cons = np.poly1d(z_cons)
        ax.plot(message_nums_cons, p_cons(message_nums_cons), 
               color='#c0392b', linewidth=2, linestyle='--', alpha=0.8)
        
        ax.set_xlabel('Message Sequence Number', fontsize=12, fontweight='bold')
        ax.set_ylabel('Latency (ms)', fontsize=12, fontweight='bold')
        ax.set_title(f'Latency vs Message Throughput\nProducer: {producer_throughput:.0f} msgs/s | Consumer: {consumer_throughput:.0f} msgs/s',
                    fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right', fontsize=11, framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path = f'{self.output_dir}/timing_vs_throughput.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Generated: {output_path}")
    
    def plot_end_to_end_pipeline(self):
        """
        Plot complete pipeline visualization showing:
        - t1: Message send time
        - t2: Kafka acknowledgment time (t2-t1)
        - t3: Consumer receive time (t3-t2)
        - Total end-to-end time (t3-t1)
        """
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Extract timing data
        send_to_ack_times = self.producer_timing.get('send_to_ack_times', [])
        kafka_to_consumer_times = self.consumer_timing.get('kafka_to_consumer_times', [])
        
        if not send_to_ack_times or not kafka_to_consumer_times:
            print("Warning: Insufficient timing data for pipeline visualization")
            return
        
        # Calculate average times for each stage
        avg_send_to_ack = np.mean([item['duration_ms'] for item in send_to_ack_times])
        avg_kafka_to_consumer = np.mean([item['duration_ms'] for item in kafka_to_consumer_times])
        avg_end_to_end = avg_send_to_ack + avg_kafka_to_consumer
        
        # Create stacked bar chart
        stages = ['Complete Pipeline']
        send_to_ack_vals = [avg_send_to_ack]
        kafka_to_consumer_vals = [avg_kafka_to_consumer]
        
        bar_width = 0.6
        
        # Plot stacked bars
        p1 = ax.barh(stages, send_to_ack_vals, bar_width, 
                    label='Producer→Kafka (t2-t1)', color='#3498db', edgecolor='black', linewidth=2)
        p2 = ax.barh(stages, kafka_to_consumer_vals, bar_width, 
                    left=send_to_ack_vals, label='Kafka→Consumer (t3-t2)', 
                    color='#e74c3c', edgecolor='black', linewidth=2)
        
        # Add value labels
        ax.text(avg_send_to_ack / 2, 0, f'{avg_send_to_ack:.2f}ms\n(t2-t1)', 
               ha='center', va='center', fontsize=12, fontweight='bold', color='white')
        ax.text(avg_send_to_ack + avg_kafka_to_consumer / 2, 0, 
               f'{avg_kafka_to_consumer:.2f}ms\n(t3-t2)', 
               ha='center', va='center', fontsize=12, fontweight='bold', color='white')
        
        # Add total time annotation
        ax.text(avg_end_to_end + 5, 0, f'Total: {avg_end_to_end:.2f}ms', 
               ha='left', va='center', fontsize=14, fontweight='bold', 
               bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7))
        
        ax.set_xlabel('Time (ms)', fontsize=12, fontweight='bold')
        ax.set_title('End-to-End Message Pipeline Timing\n(Average Latency Breakdown)', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right', fontsize=11, framealpha=0.9)
        ax.grid(axis='x', alpha=0.3)
        
        # Add throughput info as text box
        producer_throughput_mb = self.producer_data.get('throughput_mb_per_sec', 0)
        consumer_throughput_mb = self.consumer_data.get('throughput_mb_per_sec', 0)
        info_text = f"Producer Throughput: {producer_throughput_mb:.2f} MB/s\nConsumer Throughput: {consumer_throughput_mb:.2f} MB/s"
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes, 
               fontsize=10, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        output_path = f'{self.output_dir}/end_to_end_pipeline.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Generated: {output_path}")
    
    def plot_latency_distribution(self):
        """Plot distribution of latencies for both stages"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        send_to_ack_times = self.producer_timing.get('send_to_ack_times', [])
        kafka_to_consumer_times = self.consumer_timing.get('kafka_to_consumer_times', [])
        
        if not send_to_ack_times or not kafka_to_consumer_times:
            print("Warning: Insufficient timing data for distribution visualization")
            return
        
        # Extract durations
        send_to_ack_durations = [item['duration_ms'] for item in send_to_ack_times]
        kafka_to_consumer_durations = [item['duration_ms'] for item in kafka_to_consumer_times]
        
        # Plot histogram for Producer -> Kafka
        ax1.hist(send_to_ack_durations, bins=50, color='#3498db', alpha=0.7, edgecolor='black')
        ax1.axvline(np.mean(send_to_ack_durations), color='red', linestyle='--', 
                   linewidth=2, label=f'Mean: {np.mean(send_to_ack_durations):.2f}ms')
        ax1.axvline(np.percentile(send_to_ack_durations, 95), color='orange', 
                   linestyle='--', linewidth=2, label=f'P95: {np.percentile(send_to_ack_durations, 95):.2f}ms')
        ax1.set_xlabel('Latency (ms)', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Frequency', fontsize=12, fontweight='bold')
        ax1.set_title('Producer→Kafka (t2-t1)\nLatency Distribution', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(alpha=0.3)
        
        # Plot histogram for Kafka -> Consumer
        ax2.hist(kafka_to_consumer_durations, bins=50, color='#e74c3c', alpha=0.7, edgecolor='black')
        ax2.axvline(np.mean(kafka_to_consumer_durations), color='red', linestyle='--', 
                   linewidth=2, label=f'Mean: {np.mean(kafka_to_consumer_durations):.2f}ms')
        ax2.axvline(np.percentile(kafka_to_consumer_durations, 95), color='orange', 
                   linestyle='--', linewidth=2, label=f'P95: {np.percentile(kafka_to_consumer_durations, 95):.2f}ms')
        ax2.set_xlabel('Latency (ms)', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Frequency', fontsize=12, fontweight='bold')
        ax2.set_title('Kafka→Consumer (t3-t2)\nLatency Distribution', fontsize=14, fontweight='bold')
        ax2.legend()
        ax2.grid(alpha=0.3)
        
        plt.tight_layout()
        output_path = f'{self.output_dir}/latency_distribution.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Generated: {output_path}")
    
    def plot_throughput_comparison(self):
        """Compare producer and consumer throughput"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        categories = ['Producer', 'Consumer']
        throughput_mb = [
            self.producer_data.get('throughput_mb_per_sec', 0),
            self.consumer_data.get('throughput_mb_per_sec', 0)
        ]
        throughput_msgs = [
            self.producer_data.get('throughput_msgs_per_sec', 0),
            self.consumer_data.get('throughput_msgs_per_sec', 0)
        ]
        
        x = np.arange(len(categories))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, throughput_mb, width, label='MB/s', 
                      color='#3498db', alpha=0.8, edgecolor='black', linewidth=1.5)
        
        # Add secondary axis for msgs/s
        ax2 = ax.twinx()
        bars2 = ax2.bar(x + width/2, throughput_msgs, width, label='msgs/s', 
                       color='#2ecc71', alpha=0.8, edgecolor='black', linewidth=1.5)
        
        # Add value labels
        for bar, value in zip(bars1, throughput_mb):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:.2f}\nMB/s',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        for bar, value in zip(bars2, throughput_msgs):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value:.0f}\nmsgs/s',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        ax.set_xlabel('Component', fontsize=12, fontweight='bold')
        ax.set_ylabel('Throughput (MB/s)', fontsize=12, fontweight='bold', color='#3498db')
        ax2.set_ylabel('Throughput (msgs/s)', fontsize=12, fontweight='bold', color='#2ecc71')
        ax.set_title('Producer vs Consumer Throughput Comparison', fontsize=14, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(categories)
        ax.tick_params(axis='y', labelcolor='#3498db')
        ax2.tick_params(axis='y', labelcolor='#2ecc71')
        ax.grid(axis='y', alpha=0.3)
        
        # Combine legends
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=11)
        
        plt.tight_layout()
        output_path = f'{self.output_dir}/throughput_comparison.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Generated: {output_path}")
    
    def generate_all_charts(self):
        """Generate all visualization charts"""
        print("\n" + "="*60)
        print("Generating Visualization Charts")
        print("="*60 + "\n")
        
        if not self.load_data():
            print("Failed to load data. Cannot generate charts.")
            return False
        
        try:
            self.plot_timing_breakdown()
            self.plot_timing_vs_throughput()
            self.plot_end_to_end_pipeline()
            self.plot_latency_distribution()
            self.plot_throughput_comparison()
            
            print("\n" + "="*60)
            print("Chart Generation Complete!")
            print("="*60)
            return True
        except Exception as e:
            print(f"Error generating charts: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    visualizer = StressTestVisualizer()
    visualizer.generate_all_charts()
