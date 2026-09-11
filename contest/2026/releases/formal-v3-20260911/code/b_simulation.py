"""Synthetic test world, NOT the official simulator or official test results.

Source placement, orientations and coordinate-hashed noise are our experimental
assumptions. The strategy only receives protocol responses, never world objects.
"""
from dataclasses import dataclass
import hashlib
import json
import math
import random
import time


@dataclass(frozen=True)
class Source:
    channel: int
    position: tuple
    radius: float
    direction: float | None = None


class SyntheticSimulator:
    def __init__(self, sources, error_seed=0):
        self.sources = {s.channel: s for s in sources}
        if len(self.sources) != len(sources):
            raise ValueError('Channels must be unique')
        self.error_seed = error_seed
        self.position, self.channel = (0., 0.), 1
        self.virtual_time = 0.
        self.active = False
        self.cleared = set()
        self.cache = {}
        self.counts = dict(measure=0, clear=0, successful_clear=0, switch=0)
        self.distance = 0.

    def transport(self, path, raw):
        request = json.loads(raw)
        key = request['request_id']
        if key in self.cache:
            previous_path, previous_raw, previous_reply = self.cache[key]
            if path == previous_path and raw == previous_raw:
                return previous_reply
            return 409, dict(accepted=False, real_timestamp_ms=0, virtual_time_s=0)
        if path == '/enter':
            if self.active:
                return 200, dict(accepted=False, real_timestamp_ms=0, virtual_time_s=0)
            self.active = True
            fields = dict(remaining_real_duration_s=1200, max_virtual_duration_s=360000, max_real_duration_s=1200)
        elif not self.active:
            return 200, dict(accepted=False, real_timestamp_ms=0, virtual_time_s=0)
        elif path == '/exit':
            self.active = False
            fields = dict(exit_reason='user_exit')
        elif path in {'/measure', '/clear'}:
            pos = (request['position']['x'], request['position']['y'])
            channel = request['channel']
            distance = math.dist(self.position, pos)
            self.distance += distance
            self.virtual_time += distance / 5
            self.position = pos
            source = self.sources.get(channel) if channel not in self.cleared else None
            if path == '/measure':
                self.counts['measure'] += 1
                self.counts['switch'] += channel != self.channel
                self.virtual_time += 5 + (channel != self.channel)
                self.channel = channel
                fields = self._detect(source, pos)
            else:
                self.counts['clear'] += 1
                success = source is not None and math.dist(pos, source.position) <= 20
                if success:
                    self.cleared.add(channel)
                    self.counts['successful_clear'] += 1
                self.virtual_time += 5 if success else 3
                fields = dict(clear_result='success' if success else 'no_target_in_range')
        else:
            return 404, dict(accepted=False, real_timestamp_ms=0, virtual_time_s=0)
        response = 200, dict(accepted=True, real_timestamp_ms=int(time.time()*1000), virtual_time_s=round(self.virtual_time,6), **fields)
        self.cache[key] = (path, raw, response)
        return response

    def _detect(self, source, pos):
        if source is None:
            return dict(measure_result='no_signal')
        distance = math.dist(pos, source.position)
        covered = distance <= source.radius
        if source.direction is not None:
            angle = math.radians(source.direction)
            outward = (pos[0]-source.position[0])*math.cos(angle)+(pos[1]-source.position[1])*math.sin(angle)
            covered = covered and outward >= -1e-9
        if not covered:
            return dict(measure_result='no_signal')
        if distance <= 5:
            return dict(measure_result='near')
        true_angle = math.degrees(math.atan2(source.position[1]-pos[1], source.position[0]-pos[0]))
        # Fixed at a given coordinate and channel, no resampling at the same point.
        token = f'{self.error_seed}:{source.channel}:{pos[0]:.8f}:{pos[1]:.8f}'.encode()
        error = int.from_bytes(hashlib.sha256(token).digest()[:8], 'big') / (2**64-1)*2-1
        return dict(measure_result='direction', svd_deg=round((true_angle+error)%360,2)%360)


def random_case(seed, mixed=False):
    rng = random.Random(seed)
    count = rng.randint(10,16)
    sources = []
    for channel in rng.sample(range(1,21),count):
        radius, angle = 1800*math.sqrt(rng.random()), rng.random()*2*math.pi
        direction = rng.random()*360 if mixed and rng.random()<.6 else None
        sources.append(Source(channel,(radius*math.cos(angle),radius*math.sin(angle)),rng.uniform(1000,1500),direction))
    return sources
