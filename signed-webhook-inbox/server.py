import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from inbox import Inbox


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/webhooks":
            self.send_error(404)
            return
        length = self.headers.get("Content-Length", "")
        if not length.isascii() or not length.isdecimal() or len(length) > 10:
            self.send_error(400)
            return
        if int(length) > 65536:
            self.send_error(413)
            return
        self.connection.settimeout(5)
        try:
            body = self.rfile.read(int(length))
        except TimeoutError:
            self.send_error(408)
            return
        if len(body) != int(length):
            self.send_error(400)
            return
        status = self.server.inbox.accept(
            body, self.headers.get("X-Timestamp"), self.headers.get("X-Signature")
        )
        self.send_response(status)
        self.end_headers()


if __name__ == "__main__":
    secret = os.environ.get("WEBHOOK_SECRET")
    if not secret:
        raise SystemExit("Set WEBHOOK_SECRET before starting the server.")
    with ThreadingHTTPServer(("127.0.0.1", 8080), Handler) as server:
        server.inbox = Inbox("inbox.db", secret.encode())
        server.serve_forever()
