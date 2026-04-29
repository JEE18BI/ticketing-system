from flask import Flask, request, jsonify
import mysql.connector
import time

from flask_cors import CORS

app = Flask(__name__)
CORS(app)
# 🔁 Retry connection until DB is ready
def get_db_connection():
    for i in range(10):
        try:
            conn = mysql.connector.connect(
                host="db",
                user="root",
                password="root",
                database="tickets_db"
            )
            print("✅ Connected to DB")
            return conn
        except Exception as e:
            print("⏳ Waiting for DB...", e)
            time.sleep(3)

    raise Exception("❌ Could not connect to DB")


@app.route("/")
def home():
    return "Ticket Service Running"


# 🧱 Create Ticket
@app.route("/create", methods=["POST"])
def create_ticket():
    data = request.json

    conn = get_db_connection()
    cursor = conn.cursor()

    # Ensure table exists with ALL columns
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255),
        status VARCHAR(50) DEFAULT 'open',
        assigned_to VARCHAR(100)
    )
    """)

    cursor.execute(
        "INSERT INTO tickets (title, status, assigned_to) VALUES (%s, %s, %s)",
        (
            data["title"],
            data.get("status", "open"),
            data.get("assigned_to")
        )
    )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Ticket created"})


# 📥 Get all tickets
@app.route("/tickets", methods=["GET"])
def get_tickets():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Ensure table exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255),
        status VARCHAR(50) DEFAULT 'open',
        assigned_to VARCHAR(100)
    )
    """)

    cursor.execute("SELECT * FROM tickets")
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(results)


# ✏️ Update ticket (SAFE version)
@app.route("/update/<int:ticket_id>", methods=["PUT"])
def update_ticket(ticket_id):
    data = request.json

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE tickets
    SET 
        title = COALESCE(%s, title),
        status = COALESCE(%s, status),
        assigned_to = COALESCE(%s, assigned_to)
    WHERE id = %s
    """, (
        data.get("title"),
        data.get("status"),
        data.get("assigned_to"),
        ticket_id
    ))

    conn.commit()

    if cursor.rowcount == 0:
        cursor.close()
        conn.close()
        return jsonify({"error": "Ticket not found"}), 404

    cursor.close()
    conn.close()

    return jsonify({"message": "Ticket updated"})


@app.route("/delete/<int:ticket_id>", methods=["DELETE"])
def delete_ticket(ticket_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM tickets WHERE id = %s", (ticket_id,))
    conn.commit()

    if cursor.rowcount == 0:
        cursor.close()
        conn.close()
        return jsonify({"error": "Ticket not found"}), 404

    cursor.close()
    conn.close()

    return jsonify({"message": "Ticket deleted"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)