from flask import Flask, request, jsonify, Response
import os
import mysql.connector
import time
import requests
import logging
from flask_cors import CORS
from prometheus_client import Counter, Histogram, CONTENT_TYPE_LATEST, generate_latest

app = Flask(__name__)
CORS(app)

SERVICE_NAME = "ticket-service"
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s level=%(levelname)s service=ticket-service message=%(message)s"
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

DB_HOST = os.getenv("DB_HOST", "db")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
DB_NAME = os.getenv("DB_NAME", "tickets_db")

NOTIFICATION_SERVICE_URL = os.getenv(
    "NOTIFICATION_SERVICE_URL",
    "http://notification-service:5002"
)


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

# 🔁 Retry connection until DB is ready
def get_db_connection():
    for i in range(10):
        try:
            conn = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            print("✅ Connected to DB")
            return conn
        except Exception as e:
            print("⏳ Waiting for DB...", e)
            time.sleep(3)

    raise Exception("❌ Could not connect to DB")


# 🧱 Ensure table exists (clean reusable function)
def ensure_table(cursor):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255),
        status VARCHAR(50) DEFAULT 'open',
        assigned_to VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """)


@app.route("/")
def home():
    return "Ticket Service Running"


# 🧱 Create Ticket
@app.route("/create", methods=["POST"])
def create_ticket():
    data = request.json

    if not data or "title" not in data:
       return jsonify({"error": "Title is required"}), 400


    conn = get_db_connection()
    cursor = conn.cursor()

    ensure_table(cursor)

    cursor.execute(
        "INSERT INTO tickets (title, status, assigned_to) VALUES (%s, %s, %s)",
        (
            data["title"],
            data.get("status", "open"),
            data.get("assigned_to")
        )
    )

    conn.commit()

    # 🔔 Notification (safe)
    try:
        requests.post(
            f"{NOTIFICATION_SERVICE_URL}/notify",
            json={
                "event": "ticket_created",
                "title": data["title"]
            }
        )
    except Exception as e:
        print("⚠️ Notification failed:", e)

    cursor.close()
    conn.close()

    return jsonify({"message": "Ticket created"})


# 📥 Get all tickets
@app.route("/tickets", methods=["GET"])
def get_tickets():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    ensure_table(cursor)

    cursor.execute("SELECT * FROM tickets")
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(results)


# ✏️ Update ticket
@app.route("/update/<int:ticket_id>", methods=["PUT"])
def update_ticket(ticket_id):
    data = request.json or {}

    conn = get_db_connection()
    cursor = conn.cursor()

    ensure_table(cursor)

    cursor.execute("""
    UPDATE tickets
    SET 
        title = COALESCE(%s, title),
        status = COALESCE(%s, status),
        assigned_to = COALESCE(%s, assigned_to)
    WHERE id = %s
    """, (
        data.get("title"),
        data.get("status"),
        data.get("assigned_to"),
        ticket_id
    ))

    conn.commit()

    if cursor.rowcount == 0:
        cursor.close()
        conn.close()
        return jsonify({"error": "Ticket not found"}), 404

    cursor.close()
    conn.close()

    return jsonify({"message": "Ticket updated"})


# 🗑️ Delete ticket
@app.route("/delete/<int:ticket_id>", methods=["DELETE"])
def delete_ticket(ticket_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    ensure_table(cursor)

    cursor.execute("DELETE FROM tickets WHERE id = %s", (ticket_id,))
    conn.commit()

    if cursor.rowcount == 0:
        cursor.close()
        conn.close()
        return jsonify({"error": "Ticket not found"}), 404

    # 🔔 Notification (safe)
    try:
        requests.post(
            f"{NOTIFICATION_SERVICE_URL}/notify",
            json={
                "event": "ticket_deleted",
                "ticket_id": ticket_id
            }
        )
    except Exception as e:
        print("⚠️ Notification failed:", e)

    cursor.close()
    conn.close()

    return jsonify({"message": "Ticket deleted"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
