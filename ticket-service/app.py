from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host="db",
        user="root",
        password="root",
        database="tickets_db"
    )

@app.route("/")
def home():
    return "Ticket Service Running"

@app.route("/create", methods=["POST"])
def create_ticket():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS tickets (id INT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(255))")
    cursor.execute("INSERT INTO tickets (title) VALUES (%s)", (data["title"],))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Ticket saved to DB"})

@app.route("/tickets", methods=["GET"])
def get_tickets():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM tickets")
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)