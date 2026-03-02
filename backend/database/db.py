import sqlite3
import json
import uuid
from pathlib import Path

DB_PATH = Path(__file__).parent / "travel.db"
_JSON = Path(__file__).parent / "activities.json"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS activities (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            image_url TEXT,
            cancellation_policy TEXT,
            reschedule_policy TEXT
        );

        CREATE TABLE IF NOT EXISTS variations (
            id TEXT PRIMARY KEY,
            activity_id TEXT NOT NULL,
            name TEXT NOT NULL,
            timings TEXT,
            group_sizes TEXT,
            price_per_person REAL,
            currency TEXT DEFAULT 'AED',
            FOREIGN KEY (activity_id) REFERENCES activities(id)
        );

        CREATE TABLE IF NOT EXISTS bookings (
            id TEXT PRIMARY KEY,
            activity_id TEXT NOT NULL,
            variation_id TEXT NOT NULL,
            user_name TEXT,
            user_email TEXT,
            group_size INTEGER,
            booking_date TEXT,
            time_slot TEXT,
            status TEXT DEFAULT 'confirmed',
            total_price REAL,
            currency TEXT DEFAULT 'AED',
            created_at TEXT DEFAULT (datetime('now')),
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS escalations (
            id TEXT PRIMARY KEY,
            conversation_id TEXT,
            activity_requested TEXT,
            user_message TEXT,
            status TEXT DEFAULT 'pending',
            supervisor_response TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            resolved_at TEXT
        );
    """)

    count = conn.execute("SELECT COUNT(*) FROM activities").fetchone()[0]
    if count == 0:
        with open(_JSON) as f:
            activities = json.load(f)

        for act in activities:
            conn.execute(
                "INSERT INTO activities VALUES (?,?,?,?,?,?,?)",
                (act["id"], act["name"], act["description"],
                 act["category"], act["image_url"],
                 act["cancellation_policy"], act["reschedule_policy"])
            )
            for v in act["variations"]:
                conn.execute(
                    "INSERT INTO variations VALUES (?,?,?,?,?,?,?)",
                    (v["id"], act["id"], v["name"],
                     json.dumps(v["timings"]), json.dumps(v["group_sizes"]),
                     v["price_per_person"], v["currency"])
                )

    conn.commit()
    conn.close()


def search_activities(term=None, category=None):
    conn = get_conn()
    sql = "SELECT * FROM activities WHERE 1=1"
    params = []

    if term:
        sql += " AND (name LIKE ? OR description LIKE ?)"
        params += [f"%{term}%", f"%{term}%"]
    if category:
        sql += " AND category = ?"
        params.append(category)

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_activity(activity_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM activities WHERE id = ?", (activity_id,)).fetchone()
    if not row:
        conn.close()
        return None

    variations = conn.execute(
        "SELECT * FROM variations WHERE activity_id = ?", (activity_id,)
    ).fetchall()
    conn.close()

    result = dict(row)
    result["variations"] = []
    for v in variations:
        var = dict(v)
        var["timings"] = json.loads(var["timings"])
        var["group_sizes"] = json.loads(var["group_sizes"])
        result["variations"].append(var)

    return result


def save_booking(data):
    booking_id = f"BK-{str(uuid.uuid4())[:8].upper()}"
    conn = get_conn()
    conn.execute(
        """INSERT INTO bookings
           (id, activity_id, variation_id, user_name, user_email,
            group_size, booking_date, time_slot, total_price, currency, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (booking_id, data["activity_id"], data["variation_id"],
         data.get("user_name", "Guest"), data.get("user_email", ""),
         data.get("group_size", 1), data.get("booking_date"),
         data.get("time_slot"), data.get("total_price", 0),
         data.get("currency", "AED"), data.get("notes", ""))
    )
    conn.commit()
    conn.close()
    return booking_id


def save_escalation(data):
    esc_id = f"ESC-{str(uuid.uuid4())[:8].upper()}"
    conn = get_conn()
    conn.execute(
        "INSERT INTO escalations (id, conversation_id, activity_requested, user_message) VALUES (?,?,?,?)",
        (esc_id, data.get("conversation_id", ""),
         data.get("activity_requested", ""), data.get("user_message", ""))
    )
    conn.commit()
    conn.close()
    return esc_id


def resolve_escalation(esc_id, response):
    conn = get_conn()
    conn.execute(
        "UPDATE escalations SET status='resolved', supervisor_response=?, resolved_at=datetime('now') WHERE id=?",
        (response, esc_id)
    )
    conn.commit()
    conn.close()


def get_pending_escalations():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM escalations WHERE status='pending'").fetchall()
    conn.close()
    return [dict(r) for r in rows]
