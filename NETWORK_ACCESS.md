# Network Access Configuration for RankRight

## Making the App Accessible Across Your Network

### Method 1: Command Line (Recommended)

```bash
# Run with network access enabled
streamlit run app.py --server.address 0.0.0.0 --server.port 5000

# Alternative with different port
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

### Method 2: Configuration File

Create `.streamlit/config.toml` in your project directory:

```toml
[server]
headless = true
address = "0.0.0.0"
port = 5000
enableCORS = false
enableXsrfProtection = false
```

Then run normally:
```bash
streamlit run app.py
```

## Network Access Details

### What `0.0.0.0` Does
- Binds to all available network interfaces
- Makes app accessible from any device on your network
- Default `localhost` only allows access from the same machine

### Finding Your Network IP Address

**Windows:**
```cmd
ipconfig
# Look for "IPv4 Address" (usually 192.168.x.x or 10.x.x.x)
```

**macOS/Linux:**
```bash
ifconfig
# or
ip addr show
# Look for inet address (usually 192.168.x.x or 10.x.x.x)
```

### Accessing from Other Devices

Once running with `0.0.0.0`, access from any device on your network:

```
http://YOUR_COMPUTER_IP:5000
```

**Examples:**
- `http://192.168.1.100:5000`
- `http://10.0.0.50:5000`
- `http://172.16.1.25:5000`

## Firewall Configuration

### Windows Firewall
1. Open Windows Defender Firewall
2. Click "Allow an app or feature through Windows Defender Firewall"
3. Click "Change Settings" → "Allow another app"
4. Browse to your Python executable
5. Check both "Private" and "Public" networks
6. Click OK

### macOS Firewall
1. System Preferences → Security & Privacy → Firewall
2. Click "Firewall Options"
3. Add Python or allow incoming connections
4. Click OK

### Linux (UFW)
```bash
# Allow port 5000
sudo ufw allow 5000

# Or allow from specific network range
sudo ufw allow from 192.168.1.0/24 to any port 5000
```

## Security Considerations

### Production Security
- **Change default port** from 5000 to something less predictable
- **Use HTTPS** with SSL certificates for sensitive data
- **Implement authentication** if handling confidential documents
- **Restrict network access** to specific IP ranges if possible

### Environment Variables for Security
```bash
# Set authentication token (optional)
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_SERVER_ENABLE_CORS=false
```

## Troubleshooting

### Common Issues

**1. Cannot access from other devices**
```bash
# Check if app is running on 0.0.0.0
netstat -an | grep 5000
# Should show: 0.0.0.0:5000 or *:5000
```

**2. Connection refused**
- Check firewall settings
- Verify port is not blocked
- Ensure app is running on correct interface

**3. Slow loading from other devices**
- Check network bandwidth
- Try different port numbers
- Reduce concurrent connections

### Testing Network Access

**From the host machine:**
```bash
# Test local access
curl http://localhost:5000

# Test network access
curl http://YOUR_IP:5000
```

**From another device:**
```bash
# Test connectivity
ping YOUR_COMPUTER_IP
telnet YOUR_COMPUTER_IP 5000
```

## Advanced Configuration

### Multiple Network Interfaces
```bash
# Bind to specific interface
streamlit run app.py --server.address 192.168.1.100 --server.port 5000
```

### Docker Deployment (Alternative)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -r pip-requirements.txt

EXPOSE 5000
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "5000"]
```

### Reverse Proxy with Nginx (Advanced)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Quick Start Commands

### Development (Local Network)
```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 5000
```

### Production (with SSL - Advanced)
```bash
streamlit run app.py \
    --server.address 0.0.0.0 \
    --server.port 443 \
    --server.sslCertFile /path/to/cert.pem \
    --server.sslKeyFile /path/to/key.pem
```

## Mobile Access

Your app will be fully accessible on mobile devices once network access is configured:

- **iPhone/iPad**: Open Safari, navigate to `http://YOUR_IP:5000`
- **Android**: Open Chrome, navigate to `http://YOUR_IP:5000`
- **Tablets**: Works with any modern browser

The Streamlit interface is responsive and works well on mobile devices for document analysis and viewing results.