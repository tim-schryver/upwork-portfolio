import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory

from inventory import Inventory


class InventoryTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.database = Path(directory.name) / "inventory.db"
        self.inventory = Inventory(self.database)

    def test_retry_survives_restart_and_preserves_stock(self):
        self.assertEqual(self.inventory.reserve("first", "demo-widget", 7)[0], 201)
        reopened = Inventory(self.database)
        self.assertEqual(reopened.reserve("first", "demo-widget", 7)[0], 200)
        self.assertEqual(reopened.reserve("first", "demo-widget", 1)[0], 409)
        self.assertEqual(reopened.reserve("second", "demo-widget", 3)[0], 201)

    def test_concurrent_requests_cannot_oversell(self):
        def checkout(index):
            return self.inventory.reserve(str(index), "demo-widget", 2)[0]

        with ThreadPoolExecutor(max_workers=8) as pool:
            statuses = list(pool.map(checkout, range(12)))
        self.assertCountEqual(statuses, [201] * 5 + [409] * 7)

    def test_validation_and_unknown_sku(self):
        self.assertEqual(self.inventory.reserve("first", "demo-widget", True)[0], 400)
        self.assertEqual(self.inventory.reserve("first", "missing", 1)[0], 404)
