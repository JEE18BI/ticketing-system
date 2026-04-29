from flask import Flask, request, jsonify
import logging
import sys
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    stream=sys.stdout
)

@app.route("/notify", methods=["POST"])
def notify():
    data = request.json
    logging.info(f"🔔 Notification: {data}")
    return jsonify({"message": "Notification received"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)