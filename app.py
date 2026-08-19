import os
import socket
from datetime import datetime, timezone

from flask import Flask, jsonify

app = Flask(__name__)

APP_VERSION = os.environ.get("APP_VERSION", "dev")


@app.route("/")
def index():
    return jsonify(
        {
            "message": "Hello from the DevSecOps pipeline sample app!",
            "hostname": socket.gethostname(),
            "version": APP_VERSION,
            "time_utc": datetime.now(timezone.utc).isoformat(),
        }
    )


@app.route("/health")
def health():
    # Used by Kubernetes liveness/readiness probes
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
