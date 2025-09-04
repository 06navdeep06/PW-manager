"""
Keep-alive server for Replit hosting.
This creates a simple web server to prevent Replit from sleeping.
"""

from flask import Flask, jsonify
import threading
import time
import os
import logging

app = Flask(__name__)
logger = logging.getLogger(__name__)

# Bot status tracking
bot_status = {
    "started_at": time.time(),
    "last_ping": time.time(),
    "total_requests": 0,
    "status": "running"
}

@app.route('/')
def home():
    bot_status["total_requests"] += 1
    return """
    <html>
        <head><title>Discord Personal Data Bot</title></head>
        <body>
            <h1>🤖 Discord Personal Data Bot</h1>
            <p>Status: <strong>Running</strong></p>
            <p>Uptime: {:.1f} seconds</p>
            <p>Total Requests: {}</p>
            <p>Last Ping: {:.1f} seconds ago</p>
            <hr>
            <p><a href="/health">Health Check</a> | <a href="/status">Status</a></p>
        </body>
    </html>
    """.format(
        time.time() - bot_status["started_at"],
        bot_status["total_requests"],
        time.time() - bot_status["last_ping"]
    )

@app.route('/health')
def health():
    bot_status["last_ping"] = time.time()
    bot_status["total_requests"] += 1
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "uptime": time.time() - bot_status["started_at"],
        "bot_token_set": bool(os.getenv('DISCORD_BOT_TOKEN')),
        "database_exists": os.path.exists('user_data.db')
    })

@app.route('/status')
def status():
    bot_status["total_requests"] += 1
    return jsonify(bot_status)

@app.route('/ping')
def ping():
    bot_status["last_ping"] = time.time()
    bot_status["total_requests"] += 1
    return "pong"

@app.route('/metrics')
def metrics():
    """Get bot performance metrics."""
    try:
        from monitoring import monitor
        metrics = monitor.get_performance_summary()
        bot_status["total_requests"] += 1
        return jsonify(metrics)
    except ImportError:
        return jsonify({"error": "Monitoring not available"})

@app.route('/health/detailed')
def detailed_health():
    """Get detailed health information."""
    try:
        from monitoring import monitor
        health = monitor.health_check()
        bot_status["total_requests"] += 1
        return jsonify(health)
    except ImportError:
        return jsonify({"error": "Monitoring not available"})

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

