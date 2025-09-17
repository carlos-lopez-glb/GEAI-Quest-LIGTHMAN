#!/usr/bin/env python3
"""
MiniTel-Lite Protocol Demo

Demonstrates the complete MiniTel-Lite v3.0 protocol implementation.
Starts a server and connects a client to retrieve the secret.
"""

import sys
import os
import logging
import threading
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from minitel import MiniTelServer, MiniTelClient


def run_server():
    """Run the MiniTel server"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    server = MiniTelServer(host='localhost', port=8080)
    
    try:
        print("🚀 Starting MiniTel-Lite v3.0 Server...")
        server.start()
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped by user")
        server.stop()


def run_client():
    """Run the MiniTel client"""
    time.sleep(0.5)  # Give server time to start
    
    print("📡 Connecting MiniTel-Lite Client...")
    client = MiniTelClient(host='localhost', port=8080)
    
    try:
        if client.connect():
            print("✅ Connected to server")
            
            print("🔄 Running protocol sequence...")
            secret = client.run_full_sequence()
            
            if secret:
                print(f"🎉 SUCCESS! Secret retrieved: {secret}")
            else:
                print("❌ Failed to retrieve secret")
        else:
            print("❌ Failed to connect to server")
            
    except Exception as e:
        print(f"❌ Client error: {e}")
    finally:
        client.disconnect()
        print("📴 Client disconnected")


def main():
    """Main demo function"""
    print("=" * 50)
    print("   MiniTel-Lite v3.0 Protocol Demo")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == 'server':
        run_server()
    elif len(sys.argv) > 1 and sys.argv[1] == 'client':
        run_client()
    else:
        # Run both server and client
        print("🏁 Starting server and client demo...")
        
        # Start server in background
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Run client
        run_client()
        
        print("✨ Demo completed!")


if __name__ == '__main__':
    main()