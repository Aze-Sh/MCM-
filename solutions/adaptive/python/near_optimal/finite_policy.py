"""Exact finite-world AND–OR calibration, isolated from the runtime solver.

Worlds have the same known source count; distances are on a 1-D integer line,
so all costs and Bellman comparisons are rational. This calibrates a RESTRICTED
problem. Its optimum is not a lower bound for the original continuous world.
"""
from collections import deque
from fractions import Fraction as F
import math


def build_graph(worlds, positions, radius=1000, clear_radius=20):
    """Each world is a tuple of source x coordinates, one per fixed channel."""
    worlds = tuple(tuple(F(x) for x in w) for w in worlds)
    positions = tuple(F(x) for x in positions)
    if not worlds or not worlds[0] or any(len(w)!=len(worlds[0]) for w in worlds):
        raise ValueError('Finite calibration requires a fixed, positive source count')
    if not positions or len(set(positions))!=len(positions):
        raise ValueError('Positions must be nonempty and distinct')
    if any(not any(abs(x-p)<=clear_radius for p in positions) for w in worlds for x in w):
        raise ValueError('Finite action family cannot clear every candidate source')
    n = len(worlds[0]);full = (1<<n)-1
    root = (tuple(range(len(worlds))),0,-1,0)
    queue = deque([root]);graph = {};terminals = set()
    while queue:
        state = queue.popleft()
        if state in graph:
            continue
        belief,cleared,at,tuned = state
        graph[state] = {}
        if cleared==full:
            terminals.add(state);continue
        current = F(0) if at<0 else positions[at]
        for c in range(n):
            if cleared>>c&1:
                continue
            for j,q in enumerate(positions):
                for kind in ('measure','clear'):
                    groups = {}
                    for w in belief:
                        x = worlds[w][c];d = abs(q-x)
                        if kind=='clear':
                            observation = 'success' if d<=clear_radius else 'miss'
                        elif d>radius:
                            observation = 'no_signal'
                        elif d<=5:
                            observation = 'near'
                        else:
                            observation = 'right' if x>q else 'left'
                        groups.setdefault(observation,[]).append(w)
                    successors = []
                    for observation,ids in sorted(groups.items()):
                        new_cleared = cleared | (1<<c) if observation=='success' else cleared
                        nxt = (tuple(ids),new_cleared,j,c if kind=='measure' else tuned)
                        fee = (5+(c!=tuned) if kind=='measure' else 5 if observation=='success' else 3)
                        cost = abs(current-q)/5+fee
                        successors.append((observation,cost,nxt))
                        if nxt not in graph:
                            queue.append(nxt)
                    graph[state][(kind,c,j)] = tuple(successors)
    return root,graph,terminals


def solve(graph, terminals):
    """Monotone finite-horizon value iteration from +infinity.

    Positive costs imply a finite optimal proper policy has no state cycle.
    At most |S| synchronous passes suffice; no recursion/cycle-cache shortcut.
    """
    values = {s:(F(0) if s in terminals else math.inf) for s in graph}
    policy = {}
    for iteration in range(len(graph)+1):
        changed = False;updated = dict(values)
        for s,actions in graph.items():
            if s in terminals:
                continue
            choices = [(max(cost+values[t] for _,cost,t in successors),a)
                       for a,successors in actions.items()]
            if not choices:
                continue
            value,action = min(choices)
            if value<values[s]:
                changed = True;updated[s] = value;policy[s] = action
        values = updated
        if not changed:
            return values,policy,iteration+1
    raise ArithmeticError('Positive-cost finite policy iteration did not stabilize')


def optical_continuation(graph, terminals, order):
    """Commit to a finite clear-action list, skip already cleared channels."""
    values = {s:(F(0) if s in terminals else math.inf) for s in graph}
    for action in reversed(order):
        updated = dict(values)
        for s,actions in graph.items():
            if s in terminals or action not in actions:
                continue
            updated[s] = max(cost+values[t] for _,cost,t in actions[action])
        values = updated
    return values


def rollout(graph, terminals, baseline, depth):
    """Exact branches for short lookahead, then the best complete continuation."""
    values = dict(baseline)
    policy = {}
    for _ in range(depth):
        updated = dict(values)
        for s,actions in graph.items():
            if s in terminals:
                continue
            value,action = min((max(cost+values[t] for _,cost,t in nexts),a)
                               for a,nexts in actions.items())
            if value<updated[s]:
                updated[s]=value;policy[s]=action
        values = updated
    return values,policy


def calibrate(worlds, positions, depths=(0,1,2,3), **kwargs):
    root,graph,terminals = build_graph(worlds,positions,**kwargs)
    exact,policy,iterations = solve(graph,terminals)
    n = len(worlds[0])
    forward = [('clear',c,j) for c in range(n) for j in range(len(positions))]
    reverse = [('clear',c,j) for c in reversed(range(n)) for j in reversed(range(len(positions)))]
    first,second = [optical_continuation(graph,terminals,order) for order in (forward,reverse)]
    baseline = {s:min(first[s],second[s]) for s in graph}
    results = []
    for depth in depths:
        values,_ = rollout(graph,terminals,baseline,depth)
        results.append(dict(depth=depth,upper_s=float(values[root]),
                            gap_s=float(values[root]-exact[root])))
    return dict(worlds=len(worlds),sources_per_world=n,states=len(graph),
                exact_time_s=float(exact[root]),exact_fraction=str(exact[root]),
                first_action=policy[root],bellman_passes=iterations,rollout=results,
                scope='exact only for these finite worlds and actions; fixed known N')
