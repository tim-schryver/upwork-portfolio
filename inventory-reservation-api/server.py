import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from inventory import Inventory


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/reservations":
            self.send_error(404)
            return
        length = self.headers.get("Content-Length", "")
        if not length.isascii() or not length.isdecimal() or len(length) > 10:
            self.send_error(400)
            return
        if int(length) > 4096:
            self.send_error(413)
            return
        self.connection.settimeout(5)
        try:
            body = self.rfile.read(int(length))
            if len(body) != int(length):
                self.send_error(400)
                return
            request = json.loads(body.decode("utf-8"))
        except TimeoutError:
            self.send_error(408)
            return
        except (ValueError, RecursionError):
            self.send_error(400)
            return
        if not isinstance(request, dict):
            self.send_error(400)
            return
        status, response = self.server.inventory.reserve(
            request.get("request_id"), request.get("sku"), request.get("quantity")
        )
        payload = json.dumps(response).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    with ThreadingHTTPServer(("127.0.0.1", 8081), Handler) as server:
        server.inventory = Inventory("inventory.db")
        server.serve_forever()
