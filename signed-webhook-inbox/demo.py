import hmac
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

body = b'{"id":"event-42","type":"shipment.dispatched"}'
timestamp = str(int(time.time()))
signature = hmac.digest(b"local-demo", timestamp.encode() + b"." + body, "sha256").hex()
request = Request("http://127.0.0.1:8080/webhooks", data=body, headers={
    "Content-Type": "application/json",
    "X-Timestamp": timestamp,
    "X-Signature": signature,
})
for _ in range(2):
    try:
        with urlopen(request, timeout=5) as response:
            print(response.status)
    except HTTPError as error:
        print(error.code)
