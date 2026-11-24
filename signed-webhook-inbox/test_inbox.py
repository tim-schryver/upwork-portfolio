import hmac
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory

from inbox import Inbox


class InboxTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.inbox = Inbox(Path(directory.name) / "inbox.db", b"test-secret")

    def deliver(self, body=b'{"id":"event-1"}', now=1000):
        signature = hmac.digest(b"test-secret", b"1000." + body, "sha256").hex()
        return self.inbox.accept(body, "1000", signature, now)

    def test_bad_signature_and_expired_delivery(self):
        self.assertEqual(self.inbox.accept(b"{}", "1000", "incorrect", 1000), 401)
        self.assertEqual(self.deliver(now=1301), 401)

    def test_invalid_event_and_conflicting_retry(self):
        self.assertEqual(self.deliver(b"[]"), 400)
        self.assertEqual(self.deliver(), 202)
        self.assertEqual(self.deliver(b'{"id":"event-1","type":"changed"}'), 409)

    def test_concurrent_duplicate_deliveries(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            statuses = list(pool.map(lambda _: self.deliver(), range(8)))
        self.assertCountEqual(statuses, [202] + [200] * 7)
