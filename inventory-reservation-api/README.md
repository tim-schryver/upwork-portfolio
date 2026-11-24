# Inventory Reservation API

Reserve stock without overselling when customers check out concurrently or clients retry a request after a timeout.

## Run locally

Requires Python 3.10+ and uses only its standard library. Run `python3 server.py`, then try the following in a second terminal.

```sh
curl -i http://127.0.0.1:8081/reservations \
  -H 'Content-Type: application/json' \
  -d '{"request_id":"checkout-42","sku":"demo-widget","quantity":2}'
```

A fresh database starts with 10 demo widgets. The first request returns `201`, an identical retry returns `200`, and reusing the request ID for another reservation returns `409`. Insufficient stock returns `409` with a separate error code. Unknown SKUs return `404`.

A SQLite immediate transaction serializes writers before they check stock. The stock decrement and reservation commit together. This is a local, single-warehouse example with permanent reservations. Expiration, replenishment, and customer authentication are outside its scope.

Run `python3 -m unittest -v` for retry and concurrent checkout tests.
