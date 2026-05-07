import os

from flask import Flask, jsonify
import requests
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

TICKET_SERVICE_URL = os.getenv(
    "TICKET_SERVICE_URL",
    "http://ticket-service:5000"
)



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