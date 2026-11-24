"""Durable, idempotent intake for signed partner events."""
import hashlib
import hmac
import json
import sqlite3
import time
from contextlib import closing


class Inbox:
    def __init__(self, database, secret):
        self.database = database
        self.secret = secret
        with closing(sqlite3.connect(database)) as db, db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    body BLOB NOT NULL,
                    received_at INTEGER NOT NULL
                )
            """)

    def accept(self, body, timestamp, signature, now=None):
        now = int(time.time()) if now is None else now
        if len(body) > 65536:
            return 413
        if not timestamp or not timestamp.isascii() or not timestamp.isdecimal() or len(timestamp) > 12:
            return 401
        expected = hmac.digest(self.secret, timestamp.encode() + b"." + body, hashlib.sha256).hex()
        if abs(now - int(timestamp)) > 300 or not signature or not signature.isascii():
            return 401
        if not hmac.compare_digest(expected, signature):
            return 401

        try:
            event = json.loads(body.decode("utf-8"))
        except (ValueError, RecursionError):
            return 400
        event_id = event.get("id") if isinstance(event, dict) else None
        if not isinstance(event_id, str) or not event_id.isascii() or not 1 <= len(event_id) <= 128:
            return 400

        with closing(sqlite3.connect(self.database)) as db, db:
            inserted = db.execute(
                "INSERT INTO events VALUES (?, ?, ?) ON CONFLICT(id) DO NOTHING",
                (event_id, body, now),
            ).rowcount
            if inserted:
                return 202
            saved_body, = db.execute("SELECT body FROM events WHERE id = ?", (event_id,)).fetchone()
            return 200 if saved_body == body else 409
