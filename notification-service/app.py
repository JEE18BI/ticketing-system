from flask import Flask, jsonify
import pika
import json
import threading
import time
from datetime import datetime

app = Flask(__name__)

# In-memory log of notifications (in production: use a DB)
notifications = []

def handle_event(event_type, data):
    msg = None
    if event_type == "ticket_created":
        msg = f"New ticket #{data.get('ticket_id')} created: '{data.get('title')}' [{data.get('priority')} priority]"
    elif event_type == "ticket_assigned":
        msg = f"Ticket #{data.get('ticket_id')} assigned to agent: {data.get('agent')}"
    elif event_type == "ticket_resolved":
        msg = f"Ticket #{data.get('ticket_id')} resolved. Note: {data.get('resolution')}"
    elif event_type == "ticket_updated":
        msg = f"Ticket #{data.get('ticket_id')} updated — new status: {data.get('new_status')}"
    elif event_type == "ticket_closed":
        msg = f"Ticket #{data.get('ticket_id')} closed."

    if msg:
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_type,
            "message": msg
        }
        notifications.append(entry)
        print(f"[NOTIFICATION] {msg}")

def consume():
    while True:
        try:
            conn = pika.BlockingConnection(
                pika.ConnectionParameters(host="rabbitmq", heartbeat=60)
            )
            channel = conn.channel()
            channel.queue_declare(queue="ticket_events", durable=True)
            channel.basic_qos(prefetch_count=1)

            def callback(ch, method, properties, body):
                payload = json.loads(body)
                handle_event(payload.get("event"), payload.get("data", {}))
                ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(queue="ticket_events", on_message_callback=callback)
            print("[Notification Service] Listening for events...")
            channel.start_consuming()
        except Exception as e:
            print(f"RabbitMQ error, retrying in 5s: {e}")
            time.sleep(5)

@app.route("/")
def home():
    return "Notification Service Running"

@app.route("/notifications")
def get_notifications():
    return jsonify(notifications[-50:])  # last 50

@app.route("/notifications/clear", methods=["DELETE"])
def clear():
    notifications.clear()
    return jsonify({"message": "Cleared"})

if __name__ == "__main__":
    t = threading.Thread(target=consume, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5002)
