import os
import logging
import time

from flask import Flask, jsonify, request, Response
import requests
from flask_cors import CORS
from datetime import datetime
from prometheus_client import Counter, Gauge, Histogram, CONTENT_TYPE_LATEST, generate_latest

app = Flask(__name__)
CORS(app)

SERVICE_NAME = "reporting-service"
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s level=%(levelname)s service=reporting-service message=%(message)s"
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
TICKET_STATUS_TOTAL = Gauge(
    "ticket_status_total",
    "Current number of tickets by status",
    ["status"]
)
TICKETS_TOTAL = Gauge(
    "tickets_total",
    "Current total number of tickets"
)

TICKET_SERVICE_URL = os.getenv(
    "TICKET_SERVICE_URL",
    "http://ticket-service:5000"
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
    try:
        refresh_ticket_metrics()
    except Exception as e:
        logging.warning("failed_to_refresh_ticket_metrics error=%s", e)

    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)



#safe date parser
def parse_date(date_str):
    if not date_str:
        return None

    try:
        return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S GMT")
    except:
        try:
            return datetime.fromisoformat(str(date_str))
        except:
            return None


def calculate_ticket_summary(tickets):
    total = len(tickets)
    open_tickets = len([t for t in tickets if t.get("status") == "open"])
    in_progress = len([t for t in tickets if t.get("status") == "in_progress"])
    closed = len([t for t in tickets if t.get("status") == "closed"])

    agents = {}
    for t in tickets:
        agent = t.get("assigned_to")
        if agent:
            agents[agent] = agents.get(agent, 0) + 1

    resolution_times = []
    for t in tickets:
        if t.get("status") == "closed":
            created = parse_date(t.get("created_at"))
            updated = parse_date(t.get("updated_at"))

            if created and updated:
                diff = (updated - created).total_seconds()
                resolution_times.append(diff)

    avg_resolution_time = (
        sum(resolution_times) / len(resolution_times)
        if resolution_times else 0
    )
    top_agent = max(agents, key=agents.get) if agents else None
    closed_percentage = (closed / total * 100) if total > 0 else 0

    TICKETS_TOTAL.set(total)
    TICKET_STATUS_TOTAL.labels("open").set(open_tickets)
    TICKET_STATUS_TOTAL.labels("in_progress").set(in_progress)
    TICKET_STATUS_TOTAL.labels("closed").set(closed)

    return {
        "total_tickets": total,
        "status_breakdown": {
            "open": open_tickets,
            "in_progress": in_progress,
            "closed": closed
        },
        "tickets_per_agent": agents,
        "performance": {
            "closed_percentage": round(closed_percentage, 2),
            "avg_resolution_time_seconds": round(avg_resolution_time, 2)
        },
        "top_agent": top_agent
    }


def refresh_ticket_metrics():
    response = requests.get(f"{TICKET_SERVICE_URL}/tickets")
    if response.status_code != 200:
        raise Exception(f"ticket service returned {response.status_code}")

    return calculate_ticket_summary(response.json())


@app.route("/")
def home():
    return "Reporting Service Running"


@app.route("/report", methods=["GET"])
def generate_report():
    try:
        print("📊 Generating report...")

        response = requests.get(f"{TICKET_SERVICE_URL}/tickets")
        if response.status_code != 200:
            return jsonify(response.json()), response.status_code
        tickets = response.json()

        print("Tickets:", tickets)

        total = len(tickets)

        open_tickets = len([t for t in tickets if t.get("status") == "open"])
        in_progress = len([t for t in tickets if t.get("status") == "in_progress"])
        closed = len([t for t in tickets if t.get("status") == "closed"])

        agents = {}
        for t in tickets:
            agent = t.get("assigned_to")
            if agent:
                agents[agent] = agents.get(agent, 0) + 1

        
        resolution_times = []

        for t in tickets:
            if t.get("status") == "closed":
                created = parse_date(t.get("created_at"))
                updated = parse_date(t.get("updated_at"))

                if created and updated:
                    diff = (updated - created).total_seconds()
                    resolution_times.append(diff)

        avg_resolution_time = (
            sum(resolution_times) / len(resolution_times)
            if resolution_times else 0
        )

        top_agent = max(agents, key=agents.get) if agents else None

        closed_percentage = (closed / total * 100) if total > 0 else 0

        return jsonify({
            "total_tickets": total,
            "status_breakdown": {
                "open": open_tickets,
                "in_progress": in_progress,
                "closed": closed
            },
            "tickets_per_agent": agents,
            "performance": {
                "closed_percentage": round(closed_percentage, 2),
                "avg_resolution_time_seconds": round(avg_resolution_time, 2)
            },
            "top_agent": top_agent
        })

    except Exception as e:
        print("❌ REPORT ERROR:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
