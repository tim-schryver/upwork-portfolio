# Signed Webhook Inbox

Accept partner events securely and acknowledge them only after durable storage. The demo shows how to handle duplicate deliveries when a sender retries after a timeout.

## Run locally

Requires Python 3.10+ and uses only its standard library.

```sh
WEBHOOK_SECRET=local-demo python3 server.py
```

In another terminal, run `python3 demo.py`. On a fresh database, the two deliveries return `202` and `200`.

## Delivery contract

POST raw JSON with a string `id` to `/webhooks`. Send the Unix timestamp in `X-Timestamp` and lowercase hex HMAC-SHA256 of `timestamp + "." + raw_body` in `X-Signature`. Signatures expire outside a five-minute window. Identical repeats return `200`, and an existing ID with changed bytes returns `409`.

SQLite enforces event uniqueness inside the write transaction. The database contains the original payload for later processing. This example assumes one partner and one secret. It demonstrates intake only. Downstream processing, retention and TLS termination belong to a deployment layer.

Run `python3 -m unittest -v` for signature, retry and concurrency tests.
