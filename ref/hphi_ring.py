#!/usr/bin/env python3
"""Beru: gate-level HPHI1/HPHI2 ring (two FI flip-flops) and the RSYNC effect on Phi0.

Read from LD s1 (AtariAge TIA_1A_400dpi_1.jpg, 400 dpi) on 2026-11-28:
  FI legend (C1, about x 12900-13500, y 3250-4050 px):
    a = NOR(Sb, CK)   b = NOR(Rb, CK)               (master inputs: transparent at CK = 0)
    MU = NOR(a, ML)   ML = NOR(b, MU, R)            (R is a third input of the LOWER master NOR)
    Q  = NOR(CK & MU, Qb, R)                         (R is a third input of the UPPER slave NOR -> Q)
    Qb = NOR(CK & ML, Q)                             (slave: AND with CK, transparent at CK = 1)
  Ring (D5, about x 5900-7300, y 1500-2300 px): Sb1 = Q2, Rb1 = Qb2, Sb2 = Qb1, Rb2 = Q1.
  Both CK pins on the divider's CLK bus (y ~ 1637); both R pins on the RSYN line (write decode 03, LD s2).
  HPHI1 = F-NOR(Q1, Q2) (lower F NOR), HPHI2 = F-NOR(Qb1, Qb2) (upper F NOR).
  RSYN has a 40/6 pull-down gated by the buffered Phi0 pad line (LD s1 D5, next to the RSYN oval), and
  LD s2's note says the write-decode 40/6 pull-downs are driven by Phi2: so RSYN is high only while
  Phi0/Phi2 is low, and drops at the next Phi0 rise.

usage: hphi_ring.py          (needs ref/div3_netlist.py next to it)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import div3_netlist as nl

L = 456  # halves per line


def nor(*a):
    return int(not any(a))


def ring_settle(s, ck, r):
    for _ in range(50):
        old = dict(s)
        for i, (sb, rb) in ((1, (s['Q2'], s['Qb2'])), (2, (s['Qb1'], s['Q1']))):
            s['a%d' % i] = nor(sb, ck); s['b%d' % i] = nor(rb, ck)
            s['MU%d' % i] = nor(s['a%d' % i], s['ML%d' % i]); s['ML%d' % i] = nor(s['b%d' % i], s['MU%d' % i], r)
            s['Q%d' % i] = nor(ck & s['MU%d' % i], s['Qb%d' % i], r); s['Qb%d' % i] = nor(ck & s['ML%d' % i], s['Q%d' % i])
        if s == old:
            return
    raise RuntimeError('ring did not settle')


def ring(halves, q=(0, 0), rsyn=()):
    """One CLK half per step, CLK = t & 1. Returns (HPHI1, HPHI2) lists."""
    s = {}
    for i, v in ((1, q[0]), (2, q[1])):
        s.update({'Q%d' % i: v, 'Qb%d' % i: 1 - v, 'MU%d' % i: v, 'ML%d' % i: 1 - v, 'a%d' % i: 0, 'b%d' % i: 0})
    h1, h2 = [], []
    for t in range(halves):
        ring_settle(s, t & 1, int(t in rsyn))
        h1.append(nor(s['Q1'], s['Q2'])); h2.append(nor(s['Qb1'], s['Qb2']))
    return h1, h2


def segs(o):
    s, n = [], 1
    for a, b in zip(o, o[1:]):
        if a == b: n += 1
        else: s.append(n); n = 1
    return s


def check_ring():
    print('1. Free run, all 4 ring states:')
    for q in [(0, 0), (1, 0), (1, 1), (0, 1)]:
        h1, h2 = ring(40, q)
        st2 = {t & 1 for t in range(1, 40) if h2[t] and not h2[t - 1]}
        print('   start', q, 'HPHI1', ''.join(map(str, h1[:24])), 'HPHI2', ''.join(map(str, h2[:24])),
              '| HPHI2 starts in CLK =', st2, ', widths', set(segs(h2)[1:-1]))
    print('2. RSYN held for halves 17..rel-1, released at the start of half rel:')
    for q in [(0, 0), (1, 0), (1, 1), (0, 1)]:
        for rel in (20, 21):
            h1, h2 = ring(40, q, rsyn=range(17, rel))
            held = all(h1[t] for t in range(17, rel)) and not any(h2[t] for t in range(17, rel))
            first = next(t for t in range(rel, 40) if h2[t])
            print('   start', q, 'release in CLK = %d half:' % (rel & 1), 'ring held at 00 (HPHI1 = 1, HPHI2 = 0):', held,
                  '| first HPHI2 half', first - rel, 'halves after release, CLK =', first & 1)


def rsync_phi0(off=11, state=(0, 1, 0, 1)):
    """END RESPHI0 every line at odd offset `off` (CLK = 1 start, width 2, RES lags CLK: run_lag).
    One RSYNC in line 3, released at a Phi0 rise; its RESPHI0 is the first HPHI2 after release
    (+3 halves if released at a CLK falling edge, +4 at a rising edge, from check_ring)."""
    base = {l * L + off + i for l in range(8) for i in range(2)}
    o = nl.run_lag(3 * L, base, state)
    print('3. RSYNC-forced RESPHI0 at each Phi0 rise of line 2 (both PP polarities):')
    for pol in (1, 0):
        res = set()
        for t in range(2 * L + 20, 3 * L - 20):
            if o[t] != o[t - 1] and o[t] == pol:
                p = t + (4 if t & 1 else 3)
                pulses = {x for x in base if x < p - 2} | {p, p + 1} | {p + k * L + i for k in range(1, 4) for i in range(2)}
                q = nl.run_lag(p + 3 * L, pulses, state)
                w = segs(q[p - 14:p + 20])[1:-1]
                a = segs(q[p + 20:])[1:]
                res.add((p - t, min(w), max(w), min(a), max(a)))
        for d, wlo, whi, alo, ahi in sorted(res):
            print('   Phi0 rise = PP-input %s: RESPHI0 starts %d halves after the release; Phi0 half-periods around the RSYNC %d..%d, '
                  'after it %d..%d (3 = clean)' % ('rise' if pol else 'fall', d, wlo, whi, alo, ahi))


if __name__ == '__main__':
    check_ring()
    rsync_phi0()
