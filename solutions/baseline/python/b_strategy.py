"""Conservative coverage baseline with adaptive localization and finite fallback.

This is an initial strategy, not an optimality claim. It does not inspect simulator
internals and can operate on either the real client or the synthetic transport.
"""
import math
import time
import numpy as np

from b_geometry import bearing_halfplanes, enclosing_circle


ERROR_DEG = 1.01  # 1 degree physical bound plus conservative rounding/numeric margin.
STRATEGY_ID = 'coverage600-nearest-resume-adaptive8-grid20-stop16-v3'


def clip(polygon, normal, bound):
    p = np.asarray(polygon, float).reshape(-1,2)
    if len(p) == 0:
        return p
    output = []
    for start, end in zip(p, np.roll(p,-1,axis=0)):
        ds, de = float(normal @ start-bound), float(normal @ end-bound)
        inside_s, inside_e = ds <= 1e-8, de <= 1e-8
        if inside_s != inside_e:
            output.append(start+(end-start)*(ds/(ds-de)))
        if inside_e:
            output.append(end)
    # Remove adjacent numerical duplicates, retaining point/segment degeneracies.
    unique = []
    for v in output:
        if not unique or np.linalg.norm(v-unique[-1])>1e-7:
            unique.append(v)
    if len(unique)>1 and np.linalg.norm(unique[0]-unique[-1])<1e-7:
        unique.pop()
    return np.asarray(unique).reshape(-1,2)


def initial_region(position, bearing):
    p = np.asarray(position, float)
    angle = math.radians(bearing)
    u = np.array([math.cos(angle),math.sin(angle)])
    v = np.array([-u[1],u[0]])
    width = 1500*math.tan(math.radians(ERROR_DEG))
    # Triangle is an OUTER approximation of the radius-1500 bearing sector.
    polygon = np.array([p,p+1500*u-width*v,p+1500*u+width*v])
    # Circumscribed source-domain polygon, never an inscribed approximation.
    for theta in np.arange(32)*2*math.pi/32:
        polygon = clip(polygon,np.array([math.cos(theta),math.sin(theta)]),1800)
    return polygon


def update_region(polygon, position, bearing):
    a,b = bearing_halfplanes([(*position,bearing)],ERROR_DEG)
    for normal, bound in zip(a,b):
        polygon = clip(polygon,normal,bound)
    return polygon


def contains(polygon, point):
    p = np.asarray(polygon)
    if len(p)<3:
        return any(np.linalg.norm(v-point)<1e-7 for v in p)
    edge = np.roll(p,-1,axis=0)-p
    d = np.asarray(point)-p
    cross = edge[:,0]*d[:,1]-edge[:,1]*d[:,0]
    return bool(np.all(cross>=-1e-7) or np.all(cross<=1e-7))


def coverage_points(step=600.):
    if not 0<step<1000/math.sqrt(2):
        raise ValueError('Square diagonal must be shorter than minimum reception radius')
    k = math.ceil(1800/step)
    points = set()
    for i in range(-k-1,k+1):
        for j in range(-k-1,k+1):
            x0,y0 = i*step,j*step
            nx,ny = max(x0,min(0,x0+step)),max(y0,min(0,y0+step))
            if math.hypot(nx,ny)<=1800+1e-9:
                points.update([(x0,y0),(x0+step,y0),(x0,y0+step),(x0+step,y0+step)])
    # Deterministic serpentine route; adaptive detours return to this scan plan.
    rows = sorted({p[1] for p in points})
    return [p for row,y in enumerate(rows) for p in sorted((p for p in points if p[1]==y),reverse=bool(row%2))]


def fallback_points(polygon, tried=()):
    p = np.asarray(polygon)
    if not len(p):
        return []
    lo,hi = np.min(p,axis=0),np.max(p,axis=0)
    step = 20.
    output = []
    # Every point in the polygon has a cell centre within sqrt(2)*10 < 20m.
    for i in range(math.floor(lo[0]/step),math.floor(hi[0]/step)+1):
        for j in range(math.floor(lo[1]/step),math.floor(hi[1]/step)+1):
            point = np.array([(i+.5)*step,(j+.5)*step])
            if any(np.linalg.norm(point-np.asarray(old))<1e-7 for old in tried):
                continue
            distance = 0. if contains(p,point) else float('inf')
            for a,b in zip(p,np.roll(p,-1,axis=0)):
                ab = b-a
                t = np.clip((point-a)@ab/(ab@ab),0,1) if ab@ab>1e-16 else 0
                distance = min(distance,float(np.linalg.norm(point-(a+t*ab))))
            if distance<=math.sqrt(2)*10+1e-7:
                output.append(tuple(point))
    return output


class BudgetStop(RuntimeError):
    pass


def check_budget(client):
    if client.deadline is not None and time.monotonic()>client.deadline-8:
        raise BudgetStop('Real-time reserve reached')
    if client.virtual_time>client.virtual_limit-2000:
        raise BudgetStop('Virtual-time reserve reached')


def localize(client, channel, first_position, response):
    if response['measure_result']=='near':
        check_budget(client)
        client.clear(first_position,channel)
        return channel in client.cleared
    region = initial_region(first_position,response['svd_deg'])
    last_positive = np.array(first_position, float)
    measured = [last_positive.copy()]
    tried_clear = []
    for iteration in range(8):
        check_budget(client)
        if len(region)==0:
            raise ArithmeticError('Inconsistent bearing region; stop rather than discard evidence')
        center,radius = enclosing_circle(region)
        if radius <= 19.5:
            client.clear(center,channel)
            if channel in client.cleared:
                return True
            raise ArithmeticError('Certified covering clearance failed; model/protocol mismatch')
        direction = center-last_positive
        norm = np.linalg.norm(direction)
        direction = direction/norm if norm>1e-8 else np.array([1.,0.])
        lateral = np.array([-direction[1],direction[0]])
        offset = min(200.,max(30.,radius*.3))
        candidates = [center+offset*lateral,center-offset*lateral,
                      last_positive+.4*(center-last_positive)+offset*lateral,
                      last_positive+.4*(center-last_positive)-offset*lateral]
        candidates = [q for q in candidates if all(np.linalg.norm(q-old)>2 for old in measured)]
        if not candidates:
            break
        query = min(candidates,key=lambda q: np.linalg.norm(q-client.position))
        result = client.measure(query,channel)
        measured.append(query.copy())
        if result['measure_result']=='near':
            client.clear(query,channel)
            if channel in client.cleared:
                return True
        elif result['measure_result']=='direction':
            region = update_region(region,query,result['svd_deg'])
            last_positive = query
    # Finite, orientation-independent fallback. Negative radio measurements are
    # not used to over-prune a possible directional source.
    points = fallback_points(region,tried_clear)
    while points:
        check_budget(client)
        index = min(range(len(points)),key=lambda i: math.dist(points[i],client.position))
        query = points.pop(index)
        client.clear(query,channel)
        if channel in client.cleared:
            return True
    return False


def search(client):
    detected = set()
    completed = 0
    points = coverage_points()
    total_points = len(points)
    reason = 'coverage_finished'
    maximum_cleared = False
    try:
        while points:
            # Localization can finish far from the scan point that found a source.
            # Resume at the nearest still-required coverage point to absorb that
            # detour while preserving exactly the same finite coverage set.
            index = min(range(len(points)), key=lambda i: math.dist(points[i], client.position))
            point = points.pop(index)
            # Start with the currently selected uncleared channel to save a switch.
            channels = [c for c in range(1,21) if c not in client.cleared]
            if client.channel in channels:
                channels.remove(client.channel)
                channels.insert(0,client.channel)
            for channel in channels:
                check_budget(client)
                response = client.measure(point,channel)
                if response['measure_result'] in {'near','direction'}:
                    detected.add(channel)
                    if not localize(client,channel,point,response):
                        raise ArithmeticError('Fallback exhausted without clearance')
                    if len(client.cleared) == 16:
                        reason = 'known_maximum_cleared'
                        maximum_cleared = True
                        break
            if maximum_cleared:
                break
            completed += 1
    except BudgetStop as exc:
        reason = str(exc)
    return dict(cleared_count=len(client.cleared), detected_channels=sorted(detected),
                coverage_complete=completed==total_points, coverage_points_completed=completed,
                coverage_points_total=total_points,
                completion_certified=completed==total_points or len(client.cleared)==16,
                all_detected_cleared=detected<=client.cleared,
                virtual_time_s=client.virtual_time, accounted_time_s=client.accounted_time,
                average_clear_time_s=client.virtual_time/len(client.cleared) if client.cleared else None,
                stop_reason=reason)
