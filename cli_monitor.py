#!/usr/bin/env python3
"""
CLI API Status Monitor
A command-line version of the API monitor using only Python built-in libraries.
"""

import urllib.request
import urllib.error
import time
import datetime
import json
import sys
import signal
import threading
from urllib.parse import urlparse

class CLIAPIMonitor:
    def __init__(self):
        self.urls = []
        self.running = False
        
    def add_url(self, url, name=None):
        """Add a URL to monitor"""
        if name is None:
            name = url
        self.urls.append({'url': url, 'name': name})
        print(f"✅ Added: {name} ({url})")
    
    def check_url(self, url):
        """Check the status of a single URL"""
        try:
            start_time = time.time()
            req = urllib.request.Request(url, headers={
                'User-Agent': 'CLI-API-Monitor/1.0'
            })
            
            with urllib.request.urlopen(req, timeout=10) as response:
                response_time = (time.time() - start_time) * 1000
                status_code = response.getcode()
                
                if 200 <= status_code < 400:
                    status = "🟢 UP"
                else:
                    status = "🟡 WARNING"
                    
                return {
                    'status': status,
                    'response_time': round(response_time, 2),
                    'status_code': status_code,
                    'error': None
                }
                
        except urllib.error.HTTPError as e:
            response_time = (time.time() - start_time) * 1000
            return {
                'status': "🔴 DOWN",
                'response_time': round(response_time, 2),
                'status_code': e.code,
                'error': f'HTTP {e.code}: {e.reason}'
            }
        except urllib.error.URLError as e:
            response_time = (time.time() - start_time) * 1000
            return {
                'status': "🔴 DOWN",
                'response_time': round(response_time, 2),
                'status_code': None,
                'error': f'Connection Error: {str(e.reason)}'
            }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                'status': "🔴 DOWN",
                'response_time': round(response_time, 2),
                'status_code': None,
                'error': f'Error: {str(e)}'
            }
    
    def check_all_urls(self):
        """Check all URLs once"""
        if not self.urls:
            print("⚠️  No URLs to monitor. Add some URLs first.")
            return
            
        print(f"\n📊 Checking {len(self.urls)} URLs at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        for url_info in self.urls:
            url = url_info['url']
            name = url_info['name']
            
            result = self.check_url(url)
            
            # Format output
            status_line = f"{result['status']} {name}"
            if result['status_code']:
                status_line += f" (HTTP {result['status_code']})"
            status_line += f" - {result['response_time']}ms"
            
            print(status_line)
            
            if result['error']:
                print(f"   Error: {result['error']}")
            
            print(f"   URL: {url}")
            print()
    
    def monitor_continuously(self, interval=30):
        """Monitor URLs continuously"""
        self.running = True
        
        print(f"🔍 Starting continuous monitoring (checking every {interval} seconds)")
        print("Press Ctrl+C to stop")
        print("=" * 80)
        
        try:
            while self.running:
                self.check_all_urls()
                
                if self.running:  # Check again in case we were interrupted
                    print(f"⏳ Waiting {interval} seconds until next check...")
                    time.sleep(interval)
                    
        except KeyboardInterrupt:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        print("\n⏹️  Monitoring stopped.")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print('\n⏹️  Stopping monitor...')
    sys.exit(0)

def print_usage():
    """Print usage instructions"""
    print("""
🔍 CLI API Status Monitor

Usage:
  python3 cli_monitor.py [options]

Options:
  -h, --help              Show this help message
  -u, --url URL           Add a URL to monitor
  -n, --name NAME         Set display name for the last added URL
  -i, --interval SECONDS  Set monitoring interval (default: 30)
  -o, --once              Check all URLs once and exit
  -c, --continuous        Start continuous monitoring (default)

Examples:
  # Check URLs once
  python3 cli_monitor.py -u "https://api.example.com/health" -u "https://httpbin.org/status/200" -o
  
  # Continuous monitoring with custom interval
  python3 cli_monitor.py -u "https://api.example.com" -i 60 -c
  
  # Add URL with custom name
  python3 cli_monitor.py -u "https://api.example.com/health" -n "My API" -o

Default URLs (if none specified):
  - HTTPBin OK (https://httpbin.org/status/200)
  - HTTPBin 404 (https://httpbin.org/status/404)
  - JSONPlaceholder (https://jsonplaceholder.typicode.com/posts/1)
""")

def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    monitor = CLIAPIMonitor()
    interval = 30
    mode = 'continuous'
    
    # Parse command line arguments
    args = sys.argv[1:]
    i = 0
    last_url_name = None
    
    while i < len(args):
        arg = args[i]
        
        if arg in ['-h', '--help']:
            print_usage()
            return
        elif arg in ['-u', '--url']:
            if i + 1 < len(args):
                url = args[i + 1]
                name = last_url_name if last_url_name else url
                monitor.add_url(url, name)
                last_url_name = None
                i += 1
            else:
                print("❌ Error: --url requires a URL argument")
                return
        elif arg in ['-n', '--name']:
            if i + 1 < len(args):
                last_url_name = args[i + 1]
                i += 1
            else:
                print("❌ Error: --name requires a name argument")
                return
        elif arg in ['-i', '--interval']:
            if i + 1 < len(args):
                try:
                    interval = int(args[i + 1])
                    i += 1
                except ValueError:
                    print("❌ Error: --interval requires a number")
                    return
            else:
                print("❌ Error: --interval requires a number argument")
                return
        elif arg in ['-o', '--once']:
            mode = 'once'
        elif arg in ['-c', '--continuous']:
            mode = 'continuous'
        else:
            print(f"❌ Error: Unknown argument '{arg}'")
            print_usage()
            return
        
        i += 1
    
    # Add default URLs if none specified
    if not monitor.urls:
        print("📝 No URLs specified, adding default test URLs...")
        monitor.add_url('https://httpbin.org/status/200', 'HTTPBin OK')
        monitor.add_url('https://httpbin.org/status/404', 'HTTPBin 404')
        monitor.add_url('https://jsonplaceholder.typicode.com/posts/1', 'JSONPlaceholder')
    
    # Run monitoring
    if mode == 'once':
        monitor.check_all_urls()
    else:
        monitor.monitor_continuously(interval)

if __name__ == "__main__":
    main()