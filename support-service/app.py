from flask import Flask, jsonify, request
import requests
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

TICKET_SERVICE_URL = os.getenv(
    "TICKET_SERVICE_URL",
    "http://ticket-service:5000"
)

NOTIFICATION_SERVICE_URL = os.getenv(
    "NOTIFICATION_SERVICE_URL",
    "http://notification-service:5002"
)

@app.route("/")
def home():
    return "Support Service Running"


@app.route("/get-tickets")
def get_tickets():
    try:
        response = requests.get(f"{TICKET_SERVICE_URL}/tickets")
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/assign/<int:ticket_id>", methods=["POST"])
def assign_ticket(ticket_id):
    data = request.json

    if not data or "agent" not in data:
        return jsonify({"error": "Agent is required"}), 400

    agent = data["agent"]

    response = requests.put(
        f"{TICKET_SERVICE_URL}/update/{ticket_id}",
        json={
            "status": "in_progress",
            "assigned_to": agent
        }
    )
    
    if response.status_code != 200:
        return jsonify(response.json()), response.status_code

    try:
        requests.post(
            f"{NOTIFICATION_SERVICE_URL}/notify",
            json={
                "event": "ticket_assigned",
                "ticket_id": ticket_id,
                "agent": agent
            }
        )
    except Exception as e:
        print("⚠️ Notification failed:", e)

    return jsonify({"message": "Ticket assigned"})


@app.route("/close/<int:ticket_id>", methods=["PUT"])
def close_ticket(ticket_id):
    response = requests.put(
        f"{TICKET_SERVICE_URL}/update/{ticket_id}",
        json={"status": "closed"}
    )
    if response.status_code != 200:
        return jsonify(response.json()), response.status_code

    try:
        requests.post(
            f"{NOTIFICATION_SERVICE_URL}/notify",
            json={
                "event": "ticket_closed",
                "ticket_id": ticket_id
            }
        )
    except Exception as e:
        print("⚠️ Notification failed:", e)

    return jsonify({"message": "Ticket closed"})


@app.route("/respond/<int:ticket_id>", methods=["POST"])
def respond_ticket(ticket_id):
    data = request.json

    if not data or "message" not in data:
        return jsonify({"error": "Message is required"}), 400

    message = data["message"]

    print(f"💬 Response for ticket {ticket_id}: {message}")

    try:
        requests.post(
            f"{NOTIFICATION_SERVICE_URL}/notify",
            json={
                "event": "ticket_response",
                "ticket_id": ticket_id,
                "message": message
            }
        )
    except Exception as e:
        print("⚠️ Notification failed:", e)

    return jsonify({
        "message": "Response added",
        "ticket_id": ticket_id
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)