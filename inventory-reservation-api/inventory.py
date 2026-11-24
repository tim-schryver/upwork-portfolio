"""Inventory reservations with atomic stock changes and retry-safe requests."""
import sqlite3
from contextlib import closing


class Inventory:
    def __init__(self, database):
        self.database = database
        with closing(sqlite3.connect(database)) as db, db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS stock (
                    sku TEXT PRIMARY KEY,
                    available INTEGER NOT NULL CHECK (available >= 0)
                );
                CREATE TABLE IF NOT EXISTS reservations (
                    request_id TEXT PRIMARY KEY,
                    sku TEXT NOT NULL,
                    quantity INTEGER NOT NULL CHECK (quantity > 0)
                );
                INSERT INTO stock VALUES ('demo-widget', 10) ON CONFLICT DO NOTHING;
            """)

    def reserve(self, request_id, sku, quantity):
        if (
            not isinstance(request_id, str) or not request_id.isascii()
            or not 1 <= len(request_id) <= 128
            or not isinstance(sku, str) or not sku.isascii() or not 1 <= len(sku) <= 128
            or type(quantity) is not int or not 1 <= quantity <= 2**31 - 1
        ):
            return 400, {"error": "invalid_reservation"}

        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute(
                "SELECT sku, quantity FROM reservations WHERE request_id = ?", (request_id,)
            ).fetchone()
            reservation = {"request_id": request_id, "sku": sku, "quantity": quantity}
            if existing:
                if existing == (sku, quantity):
                    return 200, reservation
                return 409, {"error": "request_id_conflict"}

            stock = db.execute("SELECT available FROM stock WHERE sku = ?", (sku,)).fetchone()
            if stock is None:
                return 404, {"error": "unknown_sku"}
            if stock[0] < quantity:
                return 409, {"error": "insufficient_stock"}
            db.execute("UPDATE stock SET available = available - ? WHERE sku = ?", (quantity, sku))
            db.execute("INSERT INTO reservations VALUES (?, ?, ?)", (request_id, sku, quantity))
            return 201, reservation
