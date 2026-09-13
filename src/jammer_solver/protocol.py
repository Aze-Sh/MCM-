"""Serial HTTP+JSON adapter. Only an explicit caller can send requests."""
import http.client
import json
import math
import os
from pathlib import Path
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, ProxyHandler, build_opener
import uuid


class ProtocolError(RuntimeError): pass
class RejectedAction(ProtocolError): pass
class UncertainAction(ProtocolError): pass


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def validate_reply(path, reply):
    if not isinstance(reply, dict) or type(reply.get("accepted")) is not bool:
        raise UncertainAction("Malformed acceptance status")
    if not reply["accepted"]:
        raise RejectedAction("accepted=false: action did not execute")
    if not finite_number(reply.get("virtual_time_s")) or reply["virtual_time_s"] < 0:
        raise UncertainAction("Malformed virtual time in accepted response")
    if path == "/enter":
        seconds = reply.get("remaining_real_duration_s")
        if not finite_number(seconds) or not 0 <= seconds <= 1200 or int(seconds) != seconds:
            raise UncertainAction("Malformed remaining real duration")
        if not finite_number(reply.get("max_virtual_duration_s")) or reply["max_virtual_duration_s"] <= 0:
            raise UncertainAction("Malformed maximum virtual duration")
    elif path == "/measure":
        result = reply.get("measure_result")
        if result not in ("direction", "near", "no_signal"):
            raise UncertainAction("Unknown measure result")
        if result == "direction":
            angle = reply.get("svd_deg")
            if not finite_number(angle) or not 0 <= angle < 360:
                raise UncertainAction("Malformed bearing")
    elif path == "/clear" and reply.get("clear_result") not in ("success", "no_target_in_range"):
        raise UncertainAction("Unknown clear result")
    elif path == "/exit" and reply.get("exit_reason") != "user_exit":
        raise UncertainAction("Unknown exit result")


class HttpTransport:
    def __init__(self, robot_id, log_path, base_url="http://127.0.0.1:2026"):
        if (not 1 <= len(robot_id.encode("utf-8")) <= 64
                or any(unicodedata.category(c) in ("Cc", "Cf") for c in robot_id)):
            raise ValueError("Invalid robot_id")
        parsed = urlsplit(base_url)
        if (parsed.scheme != "http" or parsed.hostname not in ("127.0.0.1", "localhost")
                or parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password):
            raise ValueError("Use a local simulator URL without path or credentials")
        if parsed.port is None or not 1 <= parsed.port <= 65535:
            raise ValueError("A valid port is required")
        self.robot_id, self.base_url = robot_id, base_url
        self.prefix = uuid.uuid4().hex[:16]
        self.sequence = 0
        self.pending = None
        self.deadline = float("inf")
        self.opener = build_opener(ProxyHandler({}))
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        self.log = open(log_path, "x", encoding="utf-8")

    def record(self, event):
        self.log.write(json.dumps(event, ensure_ascii=False, allow_nan=False) + "\n")
        self.log.flush()
        os.fsync(self.log.fileno())

    def call(self, path, position=None, channel=None):
        if self.pending is not None:
            raise UncertainAction("An earlier request is unresolved; no new action is allowed")
        if path not in ("/enter", "/measure", "/clear", "/exit"):
            raise ValueError("Unsupported path")
        self.sequence += 1
        payload = dict(arena_id="default", robot_id=self.robot_id,
                       request_id=f"{self.prefix}-{self.sequence}")
        if path in ("/measure", "/clear"):
            if (position is None or len(position) != 2
                    or not all(finite_number(x) and abs(x) <= 2000000 for x in position)):
                raise ValueError("Invalid coordinates")
            if type(channel) is not int or not 1 <= channel <= 20:
                raise ValueError("Invalid channel")
            payload.update(position=dict(x=position[0], y=position[1]), channel=channel)
        wire = json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
        self.record(dict(event="intent", wall_time=time.time(), path=path, payload=payload))
        self.pending = dict(path=path, payload=payload)
        for attempt in range(3):
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise UncertainAction("Deadline reached with request unresolved")
            request = Request(self.base_url + path, data=wire,
                              headers={"Content-Type": "application/json"}, method="POST")
            try:
                with self.opener.open(request, timeout=min(5.0, remaining)) as response:
                    status, raw = response.status, response.read()
                reply = json.loads(raw.decode("utf-8"))
                self.record(dict(event="response", wall_time=time.time(), request_id=payload["request_id"],
                                 attempt=attempt, http_status=status, response=reply))
                if status != 200:
                    raise UncertainAction(f"Unexpected HTTP status {status}")
                try:
                    validate_reply(path, reply)
                except RejectedAction:
                    self.pending = None
                    raise
                self.pending = None
                return reply
            except HTTPError as exc:
                self.record(dict(event="http_error", request_id=payload["request_id"],
                                 status=exc.code, body=exc.read().decode("utf-8", errors="replace")))
                if exc.code >= 500 or exc.code == 409:
                    raise UncertainAction(f"HTTP {exc.code}: stop to avoid changing an uncertain state") from exc
                self.pending = None
                raise RejectedAction(f"HTTP {exc.code}: request refused") from exc
            except (URLError, TimeoutError, ConnectionError, http.client.HTTPException,
                    json.JSONDecodeError, UnicodeDecodeError) as exc:
                self.record(dict(event="connection_failure", request_id=payload["request_id"],
                                 attempt=attempt, error=str(exc)))
                if attempt == 2:
                    raise UncertainAction(f"No confirmed response for {payload['request_id']}") from exc
                time.sleep(max(0, min(.25 * (attempt + 1), self.deadline-time.monotonic())))
                # The same path, ID, and serialized bytes are used on every retry.

    def close(self):
        self.log.close()
