#!/usr/bin/env python3
"""
API URL Status Monitor
A simple web application to monitor API endpoint status using only Python built-in libraries.
"""

import http.server
import socketserver
import urllib.request
import urllib.error
import json
import threading
import time
import datetime
import os
from urllib.parse import urlparse, parse_qs

class APIMonitor:
    def __init__(self):
        self.urls = []
        self.status_data = {}
        self.monitoring = False
        self.monitor_thread = None
        
    def add_url(self, url, name=None):
        """Add a URL to monitor"""
        if name is None:
            name = url
        
        url_info = {
            'url': url,
            'name': name,
            'id': len(self.urls)
        }
        self.urls.append(url_info)
        self.status_data[url] = {
            'status': 'unknown',
            'response_time': 0,
            'last_check': None,
            'status_code': None,
            'error': None,
            'history': []
        }
        
    def remove_url(self, url_id):
        """Remove a URL from monitoring"""
        if 0 <= url_id < len(self.urls):
            url = self.urls[url_id]['url']
            self.urls.pop(url_id)
            if url in self.status_data:
                del self.status_data[url]
            # Update IDs
            for i, url_info in enumerate(self.urls):
                url_info['id'] = i
                
    def check_url(self, url):
        """Check the status of a single URL"""
        try:
            start_time = time.time()
            req = urllib.request.Request(url, headers={
                'User-Agent': 'API-Monitor/1.0'
            })
            
            with urllib.request.urlopen(req, timeout=10) as response:
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                status_code = response.getcode()
                
                return {
                    'status': 'up' if 200 <= status_code < 400 else 'warning',
                    'response_time': round(response_time, 2),
                    'status_code': status_code,
                    'error': None
                }
                
        except urllib.error.HTTPError as e:
            response_time = (time.time() - start_time) * 1000
            return {
                'status': 'down',
                'response_time': round(response_time, 2),
                'status_code': e.code,
                'error': f'HTTP Error: {e.code} {e.reason}'
            }
        except urllib.error.URLError as e:
            response_time = (time.time() - start_time) * 1000
            return {
                'status': 'down',
                'response_time': round(response_time, 2),
                'status_code': None,
                'error': f'URL Error: {str(e.reason)}'
            }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                'status': 'down',
                'response_time': round(response_time, 2),
                'status_code': None,
                'error': f'Error: {str(e)}'
            }
    
    def monitor_urls(self):
        """Monitor all URLs continuously"""
        while self.monitoring:
            for url_info in self.urls:
                url = url_info['url']
                result = self.check_url(url)
                
                # Update status data
                self.status_data[url].update(result)
                self.status_data[url]['last_check'] = datetime.datetime.now().isoformat()
                
                # Add to history (keep last 50 entries)
                history_entry = {
                    'timestamp': datetime.datetime.now().isoformat(),
                    'status': result['status'],
                    'response_time': result['response_time'],
                    'status_code': result['status_code']
                }
                self.status_data[url]['history'].append(history_entry)
                if len(self.status_data[url]['history']) > 50:
                    self.status_data[url]['history'].pop(0)
                    
            time.sleep(30)  # Check every 30 seconds
    
    def start_monitoring(self):
        """Start the monitoring thread"""
        if not self.monitoring and self.urls:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self.monitor_urls, daemon=True)
            self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

# Global monitor instance
monitor = APIMonitor()

class APIMonitorHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/' or self.path == '/index.html':
            self.serve_html()
        elif self.path == '/api/status':
            self.serve_status_json()
        elif self.path == '/api/urls':
            self.serve_urls_json()
        elif self.path.startswith('/api/history/'):
            url_id = int(self.path.split('/')[-1])
            self.serve_history_json(url_id)
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/urls':
            self.add_url()
        elif self.path.startswith('/api/urls/') and self.path.endswith('/delete'):
            url_id = int(self.path.split('/')[-2])
            self.delete_url(url_id)
        elif self.path == '/api/start':
            self.start_monitoring()
        elif self.path == '/api/stop':
            self.stop_monitoring()
        else:
            self.send_error(404)
    
    def serve_html(self):
        """Serve the main HTML page"""
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Status Monitor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { 
            background: #fff;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 30px;
            text-align: center;
        }
        h1 { color: #2d3748; font-size: 2.5rem; margin-bottom: 10px; }
        .subtitle { color: #718096; font-size: 1.1rem; }
        
        .controls {
            background: #fff;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 30px;
        }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; font-weight: 600; color: #4a5568; }
        input[type="text"], input[type="url"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input:focus { outline: none; border-color: #4299e1; }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            margin-right: 10px;
        }
        .btn-primary { background: #4299e1; color: white; }
        .btn-primary:hover { background: #3182ce; }
        .btn-success { background: #48bb78; color: white; }
        .btn-success:hover { background: #38a169; }
        .btn-danger { background: #f56565; color: white; }
        .btn-danger:hover { background: #e53e3e; }
        .btn-secondary { background: #edf2f7; color: #4a5568; }
        .btn-secondary:hover { background: #e2e8f0; }
        
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .status-card {
            background: #fff;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border-left: 4px solid #e2e8f0;
            transition: transform 0.2s;
        }
        .status-card:hover { transform: translateY(-2px); }
        
        .status-up { border-left-color: #48bb78; }
        .status-down { border-left-color: #f56565; }
        .status-warning { border-left-color: #ed8936; }
        .status-unknown { border-left-color: #a0aec0; }
        
        .status-header { display: flex; justify-content: between; align-items: center; margin-bottom: 15px; }
        .status-name { font-size: 1.3rem; font-weight: 600; color: #2d3748; }
        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        .badge-up { background: #c6f6d5; color: #22543d; }
        .badge-down { background: #fed7d7; color: #742a2a; }
        .badge-warning { background: #feebc8; color: #7b341e; }
        .badge-unknown { background: #e2e8f0; color: #4a5568; }
        
        .status-url { color: #718096; font-size: 0.9rem; margin-bottom: 15px; word-break: break-all; }
        .status-metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        .metric { text-align: center; }
        .metric-value { font-size: 1.5rem; font-weight: 700; color: #2d3748; }
        .metric-label { font-size: 0.85rem; color: #718096; text-transform: uppercase; }
        
        .status-actions { margin-top: 20px; text-align: right; }
        .no-urls {
            text-align: center;
            padding: 60px 20px;
            color: #718096;
        }
        .monitoring-status {
            display: inline-flex;
            align-items: center;
            margin-left: 20px;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
        }
        .monitoring-active { background: #c6f6d5; color: #22543d; }
        .monitoring-inactive { background: #fed7d7; color: #742a2a; }
        
        @media (max-width: 768px) {
            .container { padding: 10px; }
            .status-grid { grid-template-columns: 1fr; }
            .btn { margin-bottom: 10px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 API Status Monitor</h1>
            <p class="subtitle">Monitor your API endpoints in real-time</p>
            <span id="monitoring-status" class="monitoring-status monitoring-inactive">
                ⏸️ Monitoring Stopped
            </span>
        </div>
        
        <div class="controls">
            <h2 style="margin-bottom: 20px; color: #2d3748;">Add New URL to Monitor</h2>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div class="form-group">
                    <label for="url-input">API URL</label>
                    <input type="url" id="url-input" placeholder="https://api.example.com/health" required>
                </div>
                <div class="form-group">
                    <label for="name-input">Display Name (optional)</label>
                    <input type="text" id="name-input" placeholder="My API Service">
                </div>
            </div>
            <button class="btn btn-primary" onclick="addURL()">➕ Add URL</button>
            <button class="btn btn-success" onclick="startMonitoring()">▶️ Start Monitoring</button>
            <button class="btn btn-danger" onclick="stopMonitoring()">⏹️ Stop Monitoring</button>
            <button class="btn btn-secondary" onclick="refreshStatus()">🔄 Refresh</button>
        </div>
        
        <div id="status-container">
            <div class="no-urls">
                <h3>No URLs to monitor yet</h3>
                <p>Add some API endpoints above to get started!</p>
            </div>
        </div>
    </div>

    <script>
        let monitoringActive = false;
        
        async function addURL() {
            const url = document.getElementById('url-input').value.trim();
            const name = document.getElementById('name-input').value.trim();
            
            if (!url) {
                alert('Please enter a valid URL');
                return;
            }
            
            try {
                const response = await fetch('/api/urls', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url, name: name || url })
                });
                
                if (response.ok) {
                    document.getElementById('url-input').value = '';
                    document.getElementById('name-input').value = '';
                    await refreshStatus();
                } else {
                    alert('Failed to add URL');
                }
            } catch (error) {
                alert('Error adding URL: ' + error.message);
            }
        }
        
        async function deleteURL(urlId) {
            if (!confirm('Are you sure you want to remove this URL?')) return;
            
            try {
                const response = await fetch(`/api/urls/${urlId}/delete`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    await refreshStatus();
                } else {
                    alert('Failed to delete URL');
                }
            } catch (error) {
                alert('Error deleting URL: ' + error.message);
            }
        }
        
        async function startMonitoring() {
            try {
                const response = await fetch('/api/start', { method: 'POST' });
                if (response.ok) {
                    monitoringActive = true;
                    updateMonitoringStatus();
                    setTimeout(refreshStatus, 1000);
                }
            } catch (error) {
                alert('Error starting monitoring: ' + error.message);
            }
        }
        
        async function stopMonitoring() {
            try {
                const response = await fetch('/api/stop', { method: 'POST' });
                if (response.ok) {
                    monitoringActive = false;
                    updateMonitoringStatus();
                }
            } catch (error) {
                alert('Error stopping monitoring: ' + error.message);
            }
        }
        
        function updateMonitoringStatus() {
            const statusEl = document.getElementById('monitoring-status');
            if (monitoringActive) {
                statusEl.textContent = '✅ Monitoring Active';
                statusEl.className = 'monitoring-status monitoring-active';
            } else {
                statusEl.textContent = '⏸️ Monitoring Stopped';
                statusEl.className = 'monitoring-status monitoring-inactive';
            }
        }
        
        async function refreshStatus() {
            try {
                const [urlsResponse, statusResponse] = await Promise.all([
                    fetch('/api/urls'),
                    fetch('/api/status')
                ]);
                
                const urls = await urlsResponse.json();
                const statusData = await statusResponse.json();
                
                displayStatus(urls, statusData);
                
            } catch (error) {
                console.error('Error refreshing status:', error);
            }
        }
        
        function displayStatus(urls, statusData) {
            const container = document.getElementById('status-container');
            
            if (urls.length === 0) {
                container.innerHTML = `
                    <div class="no-urls">
                        <h3>No URLs to monitor yet</h3>
                        <p>Add some API endpoints above to get started!</p>
                    </div>
                `;
                return;
            }
            
            const statusCards = urls.map(url => {
                const status = statusData[url.url] || {};
                const statusClass = `status-${status.status || 'unknown'}`;
                const badgeClass = `badge-${status.status || 'unknown'}`;
                
                return `
                    <div class="status-card ${statusClass}">
                        <div class="status-header">
                            <div class="status-name">${url.name}</div>
                            <span class="status-badge ${badgeClass}">${status.status || 'unknown'}</span>
                        </div>
                        <div class="status-url">${url.url}</div>
                        <div class="status-metrics">
                            <div class="metric">
                                <div class="metric-value">${status.response_time || 0}ms</div>
                                <div class="metric-label">Response Time</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${status.status_code || 'N/A'}</div>
                                <div class="metric-label">Status Code</div>
                            </div>
                        </div>
                        ${status.error ? `<div style="margin-top: 15px; padding: 10px; background: #fed7d7; border-radius: 6px; font-size: 0.9rem; color: #742a2a;">${status.error}</div>` : ''}
                        ${status.last_check ? `<div style="margin-top: 10px; font-size: 0.85rem; color: #718096;">Last checked: ${new Date(status.last_check).toLocaleString()}</div>` : ''}
                        <div class="status-actions">
                            <button class="btn btn-danger" onclick="deleteURL(${url.id})">🗑️ Remove</button>
                        </div>
                    </div>
                `;
            }).join('');
            
            container.innerHTML = `<div class="status-grid">${statusCards}</div>`;
        }
        
        // Auto-refresh every 30 seconds when monitoring is active
        setInterval(() => {
            if (monitoringActive) {
                refreshStatus();
            }
        }, 30000);
        
        // Initial load
        refreshStatus();
        
        // Handle Enter key in input fields
        document.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && (e.target.id === 'url-input' || e.target.id === 'name-input')) {
                addURL();
            }
        });
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def serve_status_json(self):
        """Serve status data as JSON"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(monitor.status_data).encode())
    
    def serve_urls_json(self):
        """Serve URLs list as JSON"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(monitor.urls).encode())
    
    def serve_history_json(self, url_id):
        """Serve history data for a specific URL"""
        if 0 <= url_id < len(monitor.urls):
            url = monitor.urls[url_id]['url']
            history = monitor.status_data.get(url, {}).get('history', [])
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(history).encode())
        else:
            self.send_error(404)
    
    def add_url(self):
        """Add a new URL to monitor"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode())
            url = data.get('url')
            name = data.get('name')
            
            if url:
                monitor.add_url(url, name)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode())
            else:
                self.send_error(400)
        except Exception as e:
            self.send_error(400)
    
    def delete_url(self, url_id):
        """Delete a URL from monitoring"""
        monitor.remove_url(url_id)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'success': True}).encode())
    
    def start_monitoring(self):
        """Start monitoring"""
        monitor.start_monitoring()
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'success': True}).encode())
    
    def stop_monitoring(self):
        """Stop monitoring"""
        monitor.stop_monitoring()
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'success': True}).encode())

def main():
    """Main function to start the server"""
    PORT = 8080
    
    # Add some default URLs for demonstration
    monitor.add_url('https://httpbin.org/status/200', 'HTTPBin OK')
    monitor.add_url('https://httpbin.org/status/404', 'HTTPBin 404')
    monitor.add_url('https://jsonplaceholder.typicode.com/posts/1', 'JSONPlaceholder')
    
    with socketserver.TCPServer(("", PORT), APIMonitorHandler) as httpd:
        print(f"🚀 API Monitor Server started at http://localhost:{PORT}")
        print(f"📊 Open your browser and go to http://localhost:{PORT}")
        print("Press Ctrl+C to stop the server")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n⏹️  Server stopped by user")
            monitor.stop_monitoring()

if __name__ == "__main__":
    main()