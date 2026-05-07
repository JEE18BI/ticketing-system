from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

notifications = []  # ✅ store notifications


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