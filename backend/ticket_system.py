import sqlite3
import uuid
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "tickets.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id TEXT PRIMARY KEY,
            query TEXT,
            timestamp TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_ticket(query: str) -> str:
    ticket_id = "TKT-" + str(uuid.uuid4())[:8].upper()
    timestamp = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO tickets (id, query, timestamp, status) VALUES (?, ?, ?, ?)',
              (ticket_id, query, timestamp, 'OPEN'))
    conn.commit()
    conn.close()
    return ticket_id

def get_all_tickets():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM tickets ORDER BY timestamp DESC')
    rows = c.fetchall()
    conn.close()
    tickets = []
    for row in rows:
        tickets.append({
            "id": row[0],
            "query": row[1],
            "timestamp": row[2],
            "status": row[3]
        })
    return tickets
