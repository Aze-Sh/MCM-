"""Recompute v8 evidence and action costs from a saved solver event stream.

No planner, random source generator, or simulator truth is imported.
"""
import argparse
import json
import math
from pathlib import Path
from protocol import validate_reply
from . import geometry as g
from .state import Ledger, EvidenceError


def replay(events):
    ledger = None;position = (0.,0.);tuned = 1;virtual = 0.;receipt = None
    completed = False;actions = 0
    for event in events:
        kind = event.get('event')
        if kind=='v8_started':
            if ledger is not None:
                raise EvidenceError('Duplicate start')
            ledger = Ledger(event['problem'],event['extra_actions'])
            virtual = event['virtual_time_s']
        elif kind=='evidence_observation':
            if ledger is None or completed or receipt is not None:
                raise EvidenceError('Observation outside an active run')
            path,q,c,reply = event['path'],tuple(event['point']),event['channel'],event['reply']
            validate_reply(path,reply)
            cost = (5+(c!=tuned) if path=='/measure' else 5 if reply['clear_result']=='success' else 3)
            expected = virtual+math.dist(position,q)/5+cost
            if abs(expected-reply['virtual_time_s'])>5e-5:
                raise EvidenceError('Replayed virtual cost mismatch')
            virtual = reply['virtual_time_s'];position = q
            if path=='/measure': tuned = c
            receipt = ledger.observe(path,q,c,reply,prove=event['prove']);actions += 1
        elif kind=='rank_receipt':
            if receipt is None or any(event.get(k)!=v for k,v in receipt.items()):
                raise EvidenceError('Logged rank receipt disagrees with evidence')
            receipt = None
        elif kind=='verified_negative_pair':
            source = ledger.channels[event['channel']].source
            before = ledger.potential()
            changed = source.negative_pair(g.point(event['positive']),g.point(event['a']),g.point(event['b']))
            if (changed!=event['changed'] or before!=event['rank_before']
                    or ledger.potential()!=event['rank_after']):
                raise EvidenceError('Replayed negative pair proof mismatch')
        elif kind=='completion_checked':
            for c in sorted(ledger.unknown):
                if not ledger.channels[c].pending:
                    ledger.certify(c)
            completed = ledger.complete()
            if not completed or event['certified'] is not True:
                raise EvidenceError('Completion claim lacks sufficient evidence')
    if ledger is None or not completed or receipt is not None:
        raise EvidenceError('Incomplete evidence stream')
    return dict(verified=True,actions=actions,virtual_time_s=virtual,**ledger.summary())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log',type=Path)
    args = parser.parse_args()
    result = replay(json.loads(line) for line in args.log.read_text().splitlines() if line.strip())
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
