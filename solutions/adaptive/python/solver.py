"""Search/batch/approach state machine implementing the final mathematical design."""
from dataclasses import asdict
import time
from strategy import (Anchor, distance, paired_points, positive_update, negative_pair_update,
                      terminal_clear_point, search_points, next_search_point,
                      channel_order, preview_source_action)
from posterior import initial_region, constrain, tighten_anchor, clear_choice, omni_negative_cuts, nearest_clear_point
from strategy import annular_points, annular_update, annular_clear_disk, annular_clear_point, CLEAR_RADIUS
from routing import improve_clear_route, two_leg


class ModelMismatch(RuntimeError): pass
class BudgetStop(RuntimeError): pass


class Solver:
    def __init__(self, transport, problem, progress=None, use_history=True):
        self.io, self.problem, self.progress = transport, problem, progress
        self.remaining = search_points(problem)
        self.visited = []
        self.position, self.channel, self.virtual = (0.0, 0.0), 1, 0.0
        self.unknown = set(range(1, 21))
        self.discovered, self.cleared = set(), set()
        self.anchors, self.source_measures, self.negative_pairs = {}, {}, {}
        self.use_history = use_history
        self.regions = {}
        self.history_clears = self.history_tightenings = 0
        self.search_negatives = {c:[] for c in range(1,21)}
        self.negative_cut_count = 0
        self.next_search_committed = None
        self.route_planned_reduction_m = 0.0
        self.started = None
        self.deadline, self.max_virtual = float("inf"), 360000.0
        self.entered = self.exit_attempted = self.exit_confirmed = False
        self.certificate = False
        self.reason = "not_started"
        self.measures = self.clear_attempts = self.switches = 0
        self.travel = 0.0

    def emit(self, event, **fields):
        record = dict(event=event, virtual_time_s=self.virtual, **fields)
        self.io.record(record)
        if self.progress:
            self.progress(record)

    def budget(self, point):
        if time.monotonic() >= self.deadline - 25:
            raise BudgetStop("real_time_reserve")
        if self.virtual + distance(self.position, point)/5 + 6 >= self.max_virtual - 1:
            raise BudgetStop("virtual_time_reserve")
        limit = (236 if self.use_history else 252) if self.problem == 3 else 828
        if self.measures + self.clear_attempts >= limit:
            raise ModelMismatch("Action count exceeds the frozen strategy bound")

    def action(self, path, point, channel):
        self.budget(point)
        moved = distance(self.position, point)
        switching = int(path == "/measure" and channel != self.channel)
        response = self.io.call(path, point, channel)
        before = self.virtual
        self.position = tuple(point)
        self.travel += moved
        self.virtual = response["virtual_time_s"]
        if path == "/measure":
            self.measures += 1
            self.switches += switching
            self.channel = channel
            cost = 5 + switching
        else:
            self.clear_attempts += 1
            cost = 5 if response["clear_result"] == "success" else 3
        if abs(self.virtual - (before + moved/5 + cost)) > 5e-5:
            raise ModelMismatch("Returned virtual time disagrees with the documented action cost")
        return response

    def discover(self, channel):
        self.discovered.add(channel)
        self.unknown.discard(channel)
        if len(self.discovered) > 16:
            raise ModelMismatch("More than 16 distinct source channels")

    def clear(self, point, channel):
        response = self.action("/clear", point, channel)
        if response["clear_result"] != "success":
            raise ModelMismatch(f"Distance-certified clear failed for channel {channel}")
        self.cleared.add(channel)
        self.anchors.pop(channel, None)
        self.regions.pop(channel, None)
        self.emit("cleared", channel=channel, cleared_count=len(self.cleared))

    def scan(self, point):
        for channel in channel_order(self.channel, self.unknown):
            if len(self.discovered) == 16:
                break
            reply = self.action("/measure", point, channel)
            kind = reply["measure_result"]
            if kind == "no_signal":
                if self.use_history and self.problem == 3:
                    self.search_negatives[channel].append(tuple(point))
                continue
            self.discover(channel)
            if kind == "near":
                self.clear(point, channel)
            else:
                self.anchors[channel] = Anchor(tuple(point), reply["svd_deg"])
                if self.use_history:
                    self.regions[channel] = initial_region(self.anchors[channel],annular=True)
                    self.apply_negative_history(channel,point)
                    self.refresh_history(channel)
                self.emit("discovered", channel=channel, bearing=reply["svd_deg"])
        self.remaining.remove(point)
        self.visited.append(point)
        self.emit("search_point_done", visited=len(self.visited), remaining=len(self.remaining))

    def approach(self, channel):
        while channel not in self.cleared:
            anchor = self.anchors[channel]
            point, method = self.clear_plan(channel)
            if point is not None:
                if self.use_history:
                    point,method = self.route_clear(channel,point,method)
                self.emit("clear_planned",channel=channel,method=method,point=point)
                self.clear(point, channel)
                self.history_clears += int(method.startswith("history_"))
                return
            round_limit = 5 if self.use_history and self.problem == 3 else 6
            if anchor.rounds >= round_limit:
                raise ModelMismatch("Contraction round bound did not reach the clearance condition")
            ordered = annular_points(anchor,self.position) if self.use_history else paired_points(anchor,self.position)
            for point in ordered:
                reply = self.action("/measure", point, channel)
                self.source_measures[channel] = self.source_measures.get(channel, 0) + 1
                kind = reply["measure_result"]
                if kind == "near":
                    self.clear(point, channel)
                    return
                if kind == "direction":
                    self.anchors[channel] = (annular_update(anchor,point,reply["svd_deg"]) if self.use_history
                                             else positive_update(anchor,point,reply["svd_deg"]))
                    if self.use_history:
                        self.apply_negative_history(channel,point)
                    break
                if self.problem == 3:
                    raise ModelMismatch("Guaranteed in-range omnidirectional source returned no_signal")
            else:
                self.anchors[channel] = annular_update(anchor) if self.use_history else negative_pair_update(anchor)
                self.negative_pairs[channel] = self.negative_pairs.get(channel, 0) + 1
            if self.use_history:
                # A lone no_signal never clips the region. Only the proven
                # paired-negative contraction adds a new radial constraint.
                self.regions[channel] = constrain(self.regions[channel],self.anchors[channel],annular=True)
                self.refresh_history(channel)
            self.emit("anchor_updated", channel=channel, anchor=asdict(self.anchors[channel]))

    def refresh_history(self, channel):
        before = self.anchors[channel]
        after = tighten_anchor(before,self.regions[channel])
        self.anchors[channel] = after
        if after.bound < before.bound:
            self.history_tightenings += 1
            self.emit("history_tightened",channel=channel,before=before.bound,after=after.bound)

    def apply_negative_history(self,channel,positive):
        if self.problem == 3:
            negatives=self.search_negatives[channel]
            self.regions[channel]=omni_negative_cuts(self.regions[channel],positive,negatives)
            self.negative_cut_count+=len(negatives)

    def route_clear(self,channel,original,method):
        # Only the last pending source in a batch. Commit the next search point,
        # so the second leg is actually executed, not an unfulfilled proxy.
        if len(self.anchors)!=1 or len(self.discovered)>=16 or not self.remaining:
            return original,method
        target=next_search_point(original,self.remaining)
        options=[(original,method)]
        diagnostics=[]
        polygon=self.regions[channel]
        start=nearest_clear_point(polygon,self.position)
        if start is not None:
            candidate,diag=improve_clear_route(polygon,CLEAR_RADIUS-1e-6,start,self.position,target)
            options.append((candidate,"history_route"));diagnostics.append(diag)
        disk=annular_clear_disk(self.anchors[channel])
        if disk is not None:
            start=annular_clear_point(self.anchors[channel],self.position)
            candidate,diag=improve_clear_route([disk[0]],disk[1],start,self.position,target)
            options.append((candidate,"anchor_route"));diagnostics.append(diag)
        chosen,method=min(options,key=lambda item:two_leg(item[0],self.position,target))
        reduction=two_leg(original,self.position,target)-two_leg(chosen,self.position,target)
        self.next_search_committed=target
        self.route_planned_reduction_m+=max(0.0,reduction)
        self.emit("route_clear_planned",channel=channel,target=target,
                  two_leg_reduction_m=max(0.0,reduction),diagnostics=diagnostics)
        return chosen,method

    def clear_plan(self, channel):
        anchor = self.anchors[channel]
        if self.use_history:
            return clear_choice(anchor,self.regions[channel],self.position,annular=True)
        return terminal_clear_point(anchor,self.position),"anchor_certificate"

    def choose_source(self):
        def cost(c):
            point,_ = self.clear_plan(c)
            if point is not None:
                return distance(self.position,point)/5+5,c
            if self.use_history:
                point=annular_points(self.anchors[c],self.position)[0]
                return distance(self.position,point)/5+5+int(self.channel!=c),c
            return preview_source_action(self.anchors[c],self.position,self.channel,c)[2],c
        return min(self.anchors,key=cost)

    def run(self):
        self.started = time.monotonic()
        reply = self.io.call("/enter")
        self.entered = True
        self.virtual = reply["virtual_time_s"]
        self.max_virtual = reply["max_virtual_duration_s"]
        # Counting from before /enter is conservative when its response is delayed/retried.
        self.deadline = self.started + reply["remaining_real_duration_s"]
        self.io.deadline = self.deadline
        self.reason = "running"
        try:
            while self.remaining and len(self.discovered) < 16:
                search=self.next_search_committed
                self.next_search_committed=None
                self.scan(search if search is not None else next_search_point(self.position,self.remaining))
                while self.anchors:
                    self.approach(self.choose_source())
            if self.discovered != self.cleared or not (len(self.discovered) == 16 or not self.remaining):
                raise ModelMismatch("Completion conditions not satisfied")
            if not 10 <= len(self.discovered) <= 16:
                raise ModelMismatch("Complete search contradicts the specified source-count interval")
            self.certificate = True
            self.reason = "complete_with_certificate"
        except BudgetStop as exc:
            self.reason = str(exc)
        self.exit()
        return self.summary()

    def exit(self):
        if (not self.entered or self.exit_attempted or self.io.pending is not None
                or time.monotonic() >= self.deadline):
            return
        self.exit_attempted = True
        reply = self.io.call("/exit")
        self.virtual = reply["virtual_time_s"]
        self.exit_confirmed = True

    def summary(self):
        return dict(problem=self.problem, reason=self.reason, completion_certificate=self.certificate,
                    strategy="annular-history-route-v3" if self.use_history else "midpoint-v1",
                    negative_halfplane_count=self.negative_cut_count,
                    route_planned_reduction_m=self.route_planned_reduction_m,
                    next_search_committed=self.next_search_committed,
                    history_clear_count=self.history_clears,history_tightening_count=self.history_tightenings,
                    pending_regions=self.regions,
                    exit_confirmed=self.exit_confirmed, entered=self.entered,
                    discovered_channels=sorted(self.discovered), cleared_channels=sorted(self.cleared),
                    cleared_count=len(self.cleared), unknown_channels=sorted(self.unknown),
                    virtual_time_s=self.virtual,
                    average_clear_time_s=self.virtual/len(self.cleared) if self.cleared else None,
                    local_elapsed_s=time.monotonic()-self.started if self.started is not None else None,
                    official_program_runtime_s=None, source_total_from_simulator=None,
                    travel_m=self.travel, measure_count=self.measures, clear_attempts=self.clear_attempts,
                    switch_count=self.switches, source_measure_counts=self.source_measures,
                    negative_pair_counts=self.negative_pairs,
                    visited_search_points=self.visited, remaining_search_points=self.remaining,
                    pending_anchors={c:asdict(a) for c,a in self.anchors.items()})
