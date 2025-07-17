# 🔍 API Status Monitor

A simple Python web application that monitors API endpoint status using only built-in Python libraries. Perfect for strict environments where external libraries cannot be installed.

## Features

- **Real-time Monitoring**: Continuously monitors API endpoints every 30 seconds
- **Web Interface**: Clean, modern web UI with responsive design
- **Status Tracking**: Tracks response times, status codes, and error messages
- **History**: Maintains the last 50 status checks for each URL
- **No Dependencies**: Uses only Python built-in libraries
- **Easy Management**: Add/remove URLs through the web interface

## Requirements

- Python 3.6 or higher
- No external libraries required!

## Quick Start

1. **Run the application**:
   ```bash
   python3 api_monitor.py
   ```

2. **Open your browser** and go to:
   ```
   http://localhost:8080
   ```

3. **Add URLs to monitor**:
   - Enter the API URL (e.g., `https://api.example.com/health`)
   - Optionally provide a display name
   - Click "Add URL"

4. **Start monitoring**:
   - Click "Start Monitoring" to begin checking URLs every 30 seconds
   - View real-time status updates on the dashboard

## Built-in Libraries Used

- `http.server` - Web server
- `urllib.request` - HTTP requests for URL checking
- `json` - JSON data handling
- `threading` - Background monitoring
- `time` & `datetime` - Timing and timestamps
- `socketserver` - TCP server implementation

## API Endpoints

The application provides several REST API endpoints:

- `GET /` - Main web interface
- `GET /api/status` - Get current status of all URLs
- `GET /api/urls` - Get list of monitored URLs
- `POST /api/urls` - Add a new URL to monitor
- `POST /api/urls/{id}/delete` - Remove a URL from monitoring
- `POST /api/start` - Start monitoring
- `POST /api/stop` - Stop monitoring

## Status Types

- **🟢 UP**: HTTP status 200-399, responding normally
- **🟡 WARNING**: HTTP status 400+ but responding
- **🔴 DOWN**: Connection failed, timeout, or other error
- **⚪ UNKNOWN**: Not yet checked

## Configuration

You can modify the following in `api_monitor.py`:

- **Port**: Change `PORT = 8080` to use a different port
- **Check Interval**: Modify `time.sleep(30)` to change monitoring frequency
- **Timeout**: Adjust `timeout=10` in the URL checking function
- **History Size**: Change the history limit from 50 entries

## Default Test URLs

The application includes some default URLs for testing:
- HTTPBin status endpoints
- JSONPlaceholder API

You can remove these and add your own URLs through the web interface.

## Troubleshooting

**Port already in use**: Change the PORT variable in the script or kill the process using that port.

**URLs not accessible**: Check if the URLs are reachable from your network and that firewalls allow outbound connections.

**Permission denied**: Make sure you have permission to bind to the specified port (ports < 1024 require root privileges).

## Security Notes

- This application is intended for internal monitoring use
- Consider firewall rules if running on a server
- The web interface has no authentication built-in
- CORS is enabled for API endpoints

## License

This project uses only Python standard library components and can be used freely in any environment.