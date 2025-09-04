"""
Keep-alive server for Replit hosting.
This creates a simple web server to prevent Replit from sleeping.
"""

from flask import Flask
import threading
import time

app = Flask(__name__)

@app.route('/')
def home():
    return "Discord Personal Data Bot is running!"

@app.route('/health')
def health():
    return {"status": "healthy", "timestamp": time.time()}

def run_server():
    """Run the Flask server in a separate thread."""
    app.run(host='0.0.0.0', port=8080, debug=False)

def start_keep_alive():
    """Start the keep-alive server."""
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    print("Keep-alive server started on port 8080")

if __name__ == "__main__":
    start_keep_alive()

