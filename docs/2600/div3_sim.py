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

Usage: python3 div3_sim.py      (prints the free run and a RESPHI0 sweep)
"""

def run(halves, res_at=None, res_len=2, state=(0, 0, 0, 0)):
    l1t, q1b, m2, q2 = state
    out = []
    for t in range(halves):
        clk = t & 1
        res = res_at is not None and res_at <= t < res_at + res_len
        for _ in range(3):  # let the combinational paths settle
            if clk == 1:
                q1b, q2 = l1t, m2
            if res:
                q1b = 0
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
