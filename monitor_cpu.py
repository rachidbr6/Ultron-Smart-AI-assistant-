#!/usr/bin/env python3
"""Monitor Jarvis CPU and memory usage."""

import psutil
import time
import sys

def monitor_jarvis():
    """Monitor Python process CPU usage."""
    print("Monitoring Jarvis CPU/Memory usage...")
    print("Press Ctrl+C to stop\n")
    print("Time         | CPU %   | Memory (MB)")
    print("-" * 40)
    
    try:
        while True:
            # Find all Python processes
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                try:
                    if 'python' in proc.name().lower():
                        cpu_percent = proc.cpu_percent(interval=0.1)
                        memory_mb = proc.memory_info().rss / 1024 / 1024
                        if cpu_percent > 0.5:  # Only show processes using > 0.5% CPU
                            timestamp = time.strftime("%H:%M:%S")
                            print(f"{timestamp}    | {cpu_percent:6.1f}% | {memory_mb:7.1f}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
        sys.exit(0)

if __name__ == "__main__":
    monitor_jarvis()
