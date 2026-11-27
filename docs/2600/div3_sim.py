#!/usr/bin/env python3
"""Gate-level reading of the TIA's Phi0 divide-by-3 (LD s1 C6-D7), simulated.

Transcribed by Igris from the 400-dpi scan of the TIA-1A logic diagram sheet 1
(spec docs/2600/spec.md section 4.2). One character = one half CLK period.
CLK = the divider's top bus. Masters are transparent at CLK=0, slaves at CLK=1.

  master1: L1t = Q2        (gating NORs take Q2 / Q2b, the slave-2 outputs)
  slave1 : Q1b = L1t       (RESPHI0 is a 3rd input of the Q1b NOR -> forces Q1b=0)
  n      = NOR(Q1b, Q2)
  master2: M2  = n
  slave2 : Q2  = M2        (RESPHI0 is a 3rd input of the Q2b NOR -> Q2=1 while CLK=0)
  phi0n  = NOR(Q2, L1t)    (into the PP pad driver; PP's polarity is still [check])

Usage: python3 div3_sim.py      (prints the free run, a RESPHI0 sweep, and the per-line sweep)

q1_force: the value RESPHI0 forces on Q1b. 0 is the transcription; 1 is the variant
in which RESPHI0 forces the other slave-1 output (Beru's review of turichips#58, [check]).
"""

def run(halves, res_at=None, res_len=2, state=(0, 0, 0, 0), res_set=None, q1_force=0):
    l1t, q1b, m2, q2 = state
    out = []
    for t in range(halves):
        clk = t & 1
        res = (t in res_set) if res_set is not None else (
            res_at is not None and res_at <= t < res_at + res_len)
        for _ in range(3):  # let the combinational paths settle
            if clk == 1:
                q1b, q2 = l1t, m2
            if res:
                q1b = q1_force
                if clk == 0:
                    q2 = 1
            if clk == 0:
                l1t, m2 = q2, int(not (q1b or q2))
        out.append(int(not (q2 or l1t)))
    return out


def show(o):
    return ''.join('#' if v else '.' for v in o)


if __name__ == '__main__':
    print('free run ', show(run(40)))
    for s in [(0, 0, 0, 0), (1, 1, 1, 1), (0, 1, 0, 1), (1, 0, 1, 0)]:
        print('start', s, show(run(40, state=s)))
    for r in range(8, 20):
        o = run(40, res_at=r)
        rise = next(t for t in range(r + 3, 40) if o[t] and not o[t - 1])
        print(f'RESPHI0 at half {r:2d} (CLK={r & 1})', show(o), ' next rise +', rise - r)


def per_line(width=2, q1_force=0, lines=6, line=456):
    """RESPHI0 once per line (width halves, at every start offset in one 6-half
    period, every start state). Returns {start parity: (min, max segment length
    in halves of Phi0 after line 1)}; a segment of 1 half is a runt."""
    res = {}
    for off in range(12):
        pulses = {l * line + off + i for l in range(lines) for i in range(width)}
        for st in [(0, 0, 0, 0), (1, 1, 1, 1), (0, 1, 0, 1), (1, 0, 1, 0), (0, 0, 1, 0), (1, 0, 0, 1)]:
            o = run(lines * line, state=st, res_set=pulses, q1_force=q1_force)[line:]
            segs, n = [], 1
            for a, b in zip(o, o[1:]):
                if a == b:
                    n += 1
                else:
                    segs.append(n); n = 1
            lo, hi = min(segs[1:]), max(segs[1:])
            k = off & 1
            old = res.get(k, (99, 0))
            res[k] = (min(old[0], lo), max(old[1], hi))
    return res


if __name__ == '__main__':
    print('per-line RESPHI0 sweep: start CLK -> (min, max) Phi0 segment, halves; 3 = clean')
    for qf in (0, 1):
        for w in (1, 2, 3, 4):
            print(f'  Q1b forced to {qf}, pulse {w} half(s):', per_line(w, qf))
