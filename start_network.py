#!/usr/bin/env python3
"""
Network Startup Script for RankRight
Starts the Streamlit application with network access enabled.
"""

import os
import sys
import socket
import subprocess

def get_local_ip():
    """Get the local IP address of this machine."""
    try:
        # Connect to a dummy address to find local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "Unable to detect"

def check_port_available(port):
    """Check if a port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', port))
            return True
    except OSError:
        return False

def main():
    print("🚀 RankRight Network Startup")
    print("=" * 40)
    
    # Get network information
    local_ip = get_local_ip()
    port = 5000
    
    # Check if port is available
    if not check_port_available(port):
        print(f"⚠️  Port {port} is already in use.")
        port = 8501  # Try default Streamlit port
        if not check_port_available(port):
            print(f"⚠️  Port {port} is also in use. Trying port 8080...")
            port = 8080
    
    print(f"🌐 Local IP Address: {local_ip}")
    print(f"🔌 Port: {port}")
    print()
    print("📱 Access URLs:")
    print(f"   Local: http://localhost:{port}")
    print(f"   Network: http://{local_ip}:{port}")
    print()
    print("📋 Share this URL with others on your network:")
    print(f"   http://{local_ip}:{port}")
    print()
    print("🔥 Starting Streamlit with network access...")
    print("   Press Ctrl+C to stop the server")
    print("=" * 40)
    
    # Start Streamlit with network access
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.address", "0.0.0.0",
            "--server.port", str(port),
            "--server.headless", "true"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("\n💡 Try running manually:")
        print(f"   streamlit run app.py --server.address 0.0.0.0 --server.port {port}")

if __name__ == "__main__":
    main()