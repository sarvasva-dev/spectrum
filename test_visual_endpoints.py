import requests
import time
import subprocess
import threading
import json
import asyncio
import websockets

def test_visual_endpoints():
    print("Testing /visual/ HTML endpoint...")
    res = requests.get("http://127.0.0.1:8000/visual/")
    if res.status_code == 200 and "html" in res.text.lower():
        print("✓ /visual/ loaded successfully")
    else:
        print(f"✗ /visual/ failed with status {res.status_code}")
        
    print("Testing /api/health/ endpoint...")
    res = requests.get("http://127.0.0.1:8000/api/health/")
    if res.status_code == 200:
        print("✓ /api/health/ loaded successfully:", res.json())
    else:
        print(f"✗ /api/health/ failed with status {res.status_code}")

async def test_websocket():
    uri = "ws://127.0.0.1:8000/ws/visualizer/"
    try:
        print(f"Testing websocket at {uri}...")
        async with websockets.connect(uri) as websocket:
            print("✓ Websocket connected!")
            
            # trigger an event by hitting api health
            requests.get("http://127.0.0.1:8000/api/health/")
            
            # Wait for a message
            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print("✓ Received websocket message:", message)
    except Exception as e:
        print(f"✗ Websocket test failed: {e}")

if __name__ == "__main__":
    test_visual_endpoints()
    asyncio.run(test_websocket())
