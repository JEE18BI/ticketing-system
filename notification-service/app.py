from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import logging
import os
import time
from prometheus_client import Counter, Histogram, CONTENT_TYPE_LATEST, generate_latest

app = Flask(__name__)
CORS(app)

SERVICE_NAME = "notification-service"
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s level=%(levelname)s service=notification-service message=%(message)s"
)

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["service", "method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["service", "method", "endpoint"]
)

notifications = []  # ✅ store notifications


@app.before_request
def start_timer():
    request.start_time = time.time()


@app.after_request
def record_request_metrics(response):
    endpoint = request.endpoint or "unknown"
    latency = time.time() - request.start_time
    REQUEST_COUNT.labels(
        SERVICE_NAME,
        request.method,
        endpoint,
        str(response.status_code)
    ).inc()
    REQUEST_LATENCY.labels(SERVICE_NAME, request.method, endpoint).observe(latency)
    logging.info(
        "method=%s path=%s status=%s duration=%.4fs",
        request.method,
        request.path,
        response.status_code,
        latency
    )
    return response


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route("/notify", methods=["POST"])
def notify():
    data = request.json

    notifications.append(data)  # ✅ save it

    print(f"🔔 Notification: {data}")

    return jsonify({"message": "Notification received"})


@app.route("/notifications", methods=["GET"])
def get_notifications():
    return jsonify(notifications)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
