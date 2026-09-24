"""Serve live MLX90641 temperatures from a Melexis EVB90640/41 USB board."""

from __future__ import annotations

import argparse
import json
import logging
import math
import threading
import time
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


LOG = logging.getLogger(__name__)
STATIC_DIR = Path(__file__).with_name("static")
WIDTH = 16
HEIGHT = 12


class ThermalReader:
    def __init__(self, port: str, interval: float):
        self.port = port
        self.interval = interval
        self.lock = threading.Lock()
        self.snapshot: dict[str, Any] = {"status": "connecting", "error": None}

    def get_snapshot(self) -> dict[str, Any]:
        with self.lock:
            result = self.snapshot.copy()
        if result.get("status") == "live" and time.monotonic() - result["monotonic"] > 5:
            result["status"] = "stale"
        result.pop("monotonic", None)
        return result

    def _set(self, **values: Any) -> None:
        with self.lock:
            self.snapshot = {**self.snapshot, **values}

    def run(self) -> None:
        while True:
            device = None
            try:
                # Import inside the worker so the HTTP server can still report
                # driver errors if a deployment is missing dependencies.
                from mlx90641 import MLX90641
                from mlx90641_evb9064x import evb9064x_get_i2c_comport_url

                device = MLX90641()
                url = evb9064x_get_i2c_comport_url(self.port)
                if not url:
                    raise RuntimeError("Melexis USB board was not found")
                device.i2c_init(url)
                device.dump_eeprom()
                if device.extract_parameters() != 0:
                    raise RuntimeError("MLX90641 calibration data is invalid")
                LOG.info("Sensor connected: %s", url)

                while True:
                    started = time.monotonic()
                    device.get_frame_data()
                    ambient = device.get_ta()
                    pixels = device.calculate_to(1.0, ambient - 5.0)
                    if len(pixels) != WIDTH * HEIGHT or not all(math.isfinite(v) for v in pixels):
                        raise RuntimeError("Sensor returned an invalid temperature frame")
                    self._set(
                        status="live",
                        error=None,
                        width=WIDTH,
                        height=HEIGHT,
                        pixels=[round(v, 2) for v in pixels],
                        ambient=round(ambient, 2),
                        minimum=round(min(pixels), 2),
                        maximum=round(max(pixels), 2),
                        average=round(sum(pixels) / len(pixels), 2),
                        captured_at=datetime.now(timezone.utc).isoformat(),
                        monotonic=time.monotonic(),
                    )
                    time.sleep(max(0, self.interval - (time.monotonic() - started)))
            except Exception as exc:
                LOG.exception("Sensor read failed; retrying")
                self._set(status="disconnected", error=str(exc))
                time.sleep(3)
            finally:
                if device is not None:
                    try:
                        device.i2c_tear_down()
                    except Exception:
                        LOG.exception("Could not close sensor connection")


class ThermalHandler(BaseHTTPRequestHandler):
    reader: ThermalReader

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/api/frame":
            self._send(json.dumps(self.reader.get_snapshot(), allow_nan=False).encode(), "application/json; charset=utf-8")
        elif path in ("/", "/index.html"):
            self._send((STATIC_DIR / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif path == "/app.js":
            self._send((STATIC_DIR / "app.js").read_bytes(), "text/javascript; charset=utf-8")
        elif path == "/style.css":
            self._send((STATIC_DIR / "style.css").read_bytes(), "text/css; charset=utf-8")
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def _send(self, body: bytes, content_type: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", help="IP address to listen on")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--device", default="auto", help="Serial device or auto")
    parser.add_argument("--interval", type=float, default=0.5, help="Seconds between frames")
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error("--interval must be positive")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    reader = ThermalReader(args.device, args.interval)
    handler = type("BoundThermalHandler", (ThermalHandler,), {"reader": reader})
    threading.Thread(target=reader.run, name="thermal-reader", daemon=True).start()
    server = ThreadingHTTPServer((args.host, args.port), handler)
    LOG.info("Dashboard listening on http://%s:%d", args.host, args.port)
    server.serve_forever()


if __name__ == "__main__":
    main()
