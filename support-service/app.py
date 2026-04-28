from flask import Flask, jsonify
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return "Support Service Running"

@app.route("/get-tickets")
def get_tickets():
    response = requests.get("http://ticket-service:5000/tickets")
    return jsonify(response.json())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)