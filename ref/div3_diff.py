#!/usr/bin/env python3
"""Diff ref/div3_netlist.py against Igris's docs/2600/div3_sim.py.
usage: div3_diff.py PATH_TO_div3_sim.py"""
import importlib.util, itertools, random, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import div3_netlist as nl
spec = importlib.util.spec_from_file_location('ig', sys.argv[1]); ig = importlib.util.module_from_spec(spec); spec.loader.exec_module(ig)
STATES = [(a, b, c, d) for a in (0, 1) for b in (0, 1) for c in (0, 1) for d in (0, 1)]
orders = [nl.NAMES, nl.NAMES[::-1], random.Random(1).sample(nl.NAMES, len(nl.NAMES)), random.Random(2).sample(nl.NAMES, len(nl.NAMES))]
def seg(o):
    s, n = [], 1
    for a, b in zip(o, o[1:]):
        if a == b: n += 1
        else: s.append(n); n = 1
    return s
tot = diff = 0; examples = []
split = {'rise': [0, 0], 'fall': [0, 0]}  # RESΦ0 ends at CLK rising / falling edge: [runs, diffs]
for st in STATES:
    # free run
    a = ig.run(60, state=st)
    for oi, od in enumerate(orders):
        b, bad = nl.run(60, state=st, order=od)
        tot += 1
        if a[6:] != b[6:]:
            diff += 1; examples.append(('free', st, oi))
for w in (1, 2, 3, 4):
  for off in range(12):
    rs = set(range(off + 20, off + 20 + w))
    for st in STATES:
        a = ig.run(60, state=st, res_set=rs)
        for oi, od in enumerate(orders):
            b, bad = nl.run(60, state=st, res_set=rs, order=od)
            tot += 1
            k = 'rise' if (off + 20 + w) & 1 else 'fall'
            split[k][0] += 1
            if a != b:
                diff += 1; split[k][1] += 1
                if len(examples) < 12: examples.append(('res', w, off, st, oi, ''.join(map(str, a[18:50])), ''.join(map(str, b[18:50])), bad))
print('compared', tot, 'runs; differences', diff)
for k, (n, d) in split.items(): print('RESΦ0 ends at CLK', k, ':', n, 'runs,', d, 'differ')
for e in examples: print(e)
