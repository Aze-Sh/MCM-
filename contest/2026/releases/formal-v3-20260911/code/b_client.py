"""Serial CUMCM B client. Passwords are not part of this protocol.

Transport injection permits tests without touching the official simulator.
After exhausted transport retries, an uncertain action stays pending: a different
action is forbidden until the same request has a definitive response.
"""
import json
import math
from pathlib import Path
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, ProxyHandler, build_opener
import uuid


class ProtocolError(RuntimeError):
    pass


class UncertainAction(ProtocolError):
    pass


class RobotClient:
    def __init__(self, robot_id, base_url='http://127.0.0.1:2026', *, transport=None,
                 log_path=None, retries=2, retry_delay=.1, timeout=3.):
        if not isinstance(robot_id, str) or not 1 <= len(robot_id.encode('utf-8')) <= 64:
            raise ValueError('robot_id must be 1..64 UTF-8 bytes')
        if any(unicodedata.category(c).startswith('C') for c in robot_id):
            raise ValueError('Control/format characters forbidden in robot_id')
        url = urlsplit(base_url)
        if url.scheme != 'http' or url.hostname not in {'127.0.0.1', 'localhost'} or url.path not in {'', '/'} or url.query or url.fragment or url.username:
            raise ValueError('Use the local simulator HTTP origin')
        if retries < 0 or timeout <= 0 or retry_delay < 0:
            raise ValueError('Invalid retry settings')
        self.robot_id, self.base_url = robot_id, base_url.rstrip('/')
        self.retries, self.retry_delay, self.timeout = retries, retry_delay, timeout
        self.transport = transport or self._http
        self.log_path = Path(log_path) if log_path else None
        self.position, self.channel = (0., 0.), 1
        self.virtual_time = self.accounted_time = 0.
        self.cleared = set()
        self.active, self.deadline = False, None
        self.virtual_limit = 360000.
        self._pending = None
        self._opener = build_opener(ProxyHandler({}))

    def _http(self, path, raw):
        timeout = self.timeout
        if self.deadline is not None:
            timeout = min(timeout, max(.01, self.deadline - time.monotonic()))
        req = Request(self.base_url + path, data=raw, headers={'Content-Type': 'application/json'}, method='POST')
        try:
            with self._opener.open(req, timeout=timeout) as response:
                return response.status, json.loads(response.read().decode('utf-8'))
        except HTTPError as exc:
            try:
                payload = json.loads(exc.read().decode('utf-8'))
            except (ValueError, UnicodeError):
                payload = {}
            return exc.code, payload

    def _log(self, path, raw, **result):
        if self.log_path:
            payload = json.loads(raw)
            payload.pop('robot_id', None)
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(dict(path=path, request=payload, **result), ensure_ascii=False, allow_nan=False) + '\n')

    def _action(self, path, fields):
        signature = (path, json.dumps(fields, sort_keys=True, allow_nan=False))
        if self._pending:
            if self._pending[0] != signature:
                raise UncertainAction('Resolve the previous action with the identical request first')
            raw = self._pending[1]
        else:
            if path == '/enter' and self.active:
                raise ProtocolError('Already entered')
            if path != '/enter' and not self.active:
                raise ProtocolError('Enter before sending actions')
            raw = json.dumps(dict(arena_id='default', robot_id=self.robot_id,
                                  request_id=uuid.uuid4().hex, **fields), allow_nan=False).encode('utf-8')
            self._pending = (signature, raw, time.monotonic())
        started = self._pending[2]
        for attempt in range(self.retries + 1):
            if self.deadline is not None and time.monotonic() >= self.deadline:
                raise UncertainAction('Real-time budget exhausted; no additional request sent')
            try:
                status, response = self.transport(path, raw)
            except (OSError, URLError, TimeoutError, ValueError) as exc:
                self._log(path, raw, error=type(exc).__name__, attempt=attempt)
                if attempt == self.retries:
                    raise UncertainAction('No definitive response; request retained for identical retry') from exc
                time.sleep(min(self.retry_delay, max(0., self.deadline-time.monotonic())) if self.deadline else self.retry_delay)
                continue
            self._log(path, raw, http_status=status, response=response, attempt=attempt)
            if not isinstance(response, dict):
                raise UncertainAction('Malformed response; action outcome unknown')
            if status == 200 and not isinstance(response.get('accepted'), bool):
                raise UncertainAction('Missing boolean accepted; action outcome unknown')
            if status != 200 or response.get('accepted') is not True:
                # 5xx may follow a partial server failure: do not permit a new action.
                if status >= 500 or status == 409:
                    raise UncertainAction(f'HTTP {status}; cannot reconcile action outcome')
                self._pending = None
                raise ProtocolError(f'Action refused: HTTP {status}, accepted={response.get("accepted")}')
            self._apply(path, fields, response, started)
            self._pending = None
            return response
        raise AssertionError('Unreachable')

    def _apply(self, path, fields, response, started):
        t = response.get('virtual_time_s')
        if isinstance(t, bool) or not isinstance(t, (int, float)) or not math.isfinite(t) or t < self.virtual_time:
            raise UncertainAction('Invalid/nonmonotone virtual time; state not updated')
        delta = 0.
        if path == '/enter':
            remaining = response.get('remaining_real_duration_s')
            if isinstance(remaining, bool) or not isinstance(remaining, (int,float)) or not 0 <= remaining <= 1200:
                raise UncertainAction('Missing/invalid remaining real duration')
            self.deadline = started + remaining
            self.virtual_limit = response.get('max_virtual_duration_s', 360000.)
            self.active = True
        elif path in {'/measure', '/clear'}:
            new_position = (fields['position']['x'], fields['position']['y'])
            delta = math.dist(self.position, new_position) / 5
            if path == '/measure':
                result = response.get('measure_result')
                bearing = response.get('svd_deg')
                if result not in {'direction', 'near', 'no_signal'} or (result == 'direction' and (isinstance(bearing,bool) or not isinstance(bearing,(int,float)) or not 0 <= bearing < 360)):
                    raise UncertainAction('Invalid detection response')
                delta += 5 + (fields['channel'] != self.channel)
                self.channel = fields['channel']
            else:
                result = response.get('clear_result')
                if result not in {'success', 'no_target_in_range'}:
                    raise UncertainAction('Invalid clear response')
                delta += 5 if result == 'success' else 3
                if result == 'success':
                    self.cleared.add(fields['channel'])
            self.position = new_position
        elif path == '/exit':
            if response.get('exit_reason') != 'user_exit':
                raise UncertainAction('Unexpected exit result')
            self.active = False
        self.accounted_time += delta
        self.virtual_time = float(t)

    @staticmethod
    def _fields(position, channel):
        if isinstance(channel,bool) or not isinstance(channel,int) or not 1 <= channel <= 20:
            raise ValueError('Channel must be an integer in 1..20')
        if len(position) != 2 or any(isinstance(x,bool) or not math.isfinite(x) or abs(x)>2000000 for x in position):
            raise ValueError('Position must contain two finite coordinates within the allowed bounds')
        return dict(position=dict(x=float(position[0]), y=float(position[1])), channel=channel)

    def enter(self):
        return self._action('/enter', {})

    def measure(self, position, channel):
        return self._action('/measure', self._fields(position, channel))

    def clear(self, position, channel):
        return self._action('/clear', self._fields(position, channel))

    def exit(self):
        return self._action('/exit', {})
