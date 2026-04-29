from flask import Flask, jsonify, request
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
@app.route("/")
def home():
    return "Support Service Running"

@app.route("/get-tickets")
def get_tickets():
    response = requests.get("http://ticket-service:5000/tickets")
    return jsonify(response.json())
@app.route("/assign/<int:ticket_id>", methods=["POST"])
def assign_ticket(ticket_id):
    data = request.json

    if not data or "agent" not in data:
        return jsonify({"error": "Agent is required"}), 400

    agent = data["agent"]

    # update ticket
    response = requests.put(
        f"http://ticket-service:5000/update/{ticket_id}",
        json={
            "status": "in_progress",
            "assigned_to": agent
        }
    )

    if response.status_code != 200:
        return jsonify({
            "error": "Failed to update ticket",
            "details": response.text
        }), 500

    # notify (safe)
    try:
        requests.post(
            "http://notification-service:5002/notify",
            json={
                "event": "ticket_assigned",
                "ticket_id": ticket_id,
                "agent": agent
            }
        )
    except Exception as e:
        print("⚠️ Notification failed:", e)

    return jsonify({
        "message": "Ticket assigned",
        "ticket_service_response": response.json()
    })
    
@app.route("/close/<int:ticket_id>", methods=["PUT"])
def close_ticket(ticket_id):
    response = requests.put(
        f"http://ticket-service:5000/update/{ticket_id}",
        json={"status": "closed"}
    )

    return jsonify({
        "message": "Ticket closed",
        "ticket_service_response": response.json()
    })
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)