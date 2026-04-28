from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

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
    agent = data.get("agent", "default-agent")

    response = requests.put(
        f"http://ticket-service:5000/update/{ticket_id}",
        json={
            "status": "in_progress",
            "assigned_to": agent
        }
    )

    return jsonify({
        "message": "Ticket assigned",
        "ticket_service_response": response.json()
    })
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)