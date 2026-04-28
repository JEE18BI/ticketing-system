from flask import Flask, jsonify
import requests
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)

TICKET_SERVICE = "http://ticket-service:5000"

@app.route("/")
def home():
    return "Reporting Service Running"

@app.route("/report/summary")
def summary():
    """Overall ticket counts by status and priority."""
    try:
        resp = requests.get(f"{TICKET_SERVICE}/stats", timeout=5)
        raw = resp.json()

        by_status = defaultdict(int)
        by_priority = defaultdict(int)
        total = 0

        for row in raw:
            by_status[row["status"]] += row["count"]
            by_priority[row["priority"]] += row["count"]
            total += row["count"]

        return jsonify({
            "generated_at": datetime.utcnow().isoformat(),
            "total_tickets": total,
            "by_status": dict(by_status),
            "by_priority": dict(by_priority)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/report/tickets")
def all_tickets():
    """Full ticket list with computed response time."""
    try:
        resp = requests.get(f"{TICKET_SERVICE}/tickets", timeout=5)
        tickets = resp.json()

        open_count = sum(1 for t in tickets if t.get("status") == "open")
        in_progress = sum(1 for t in tickets if t.get("status") == "in_progress")
        resolved = sum(1 for t in tickets if t.get("status") == "resolved")
        closed = sum(1 for t in tickets if t.get("status") == "closed")

        return jsonify({
            "generated_at": datetime.utcnow().isoformat(),
            "tickets": tickets,
            "overview": {
                "open": open_count,
                "in_progress": in_progress,
                "resolved": resolved,
                "closed": closed,
                "total": len(tickets)
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/report/agents")
def agent_report():
    """Tickets per agent."""
    try:
        resp = requests.get(f"{TICKET_SERVICE}/tickets", timeout=5)
        tickets = resp.json()

        agent_counts = defaultdict(lambda: {"assigned": 0, "resolved": 0})
        for t in tickets:
            agent = t.get("assigned_to") or "unassigned"
            agent_counts[agent]["assigned"] += 1
            if t.get("status") in ("resolved", "closed"):
                agent_counts[agent]["resolved"] += 1

        return jsonify({
            "generated_at": datetime.utcnow().isoformat(),
            "agents": dict(agent_counts)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
