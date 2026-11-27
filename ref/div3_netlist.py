#!/usr/bin/env python3
"""Beru's independent gate-level transcription of the TIA phi0 divide-by-3
(LD s1, 400 dpi, AtariAge TIA_1A_400dpi_1.jpg; divider at about x 2900-5500, y 1650-2400 px).

Every gate is kept explicit, with BOTH outputs of every NOR latch (div3_sim.py keeps
one output per latch and derives the other). Read independently of docs/2600/div3_sim.py.

  CLK bus (top, y ~ 1645): masters' input NORs take CLK (transparent at CLK=0),
                           slaves' ANDs take CLK (transparent at CLK=1).
  master 1: IU1 = NOR(Q2U, CLK)     IL1 = NOR(Q2L, CLK)
            M1U = NOR(IU1, M1L)     M1L = NOR(IL1, M1U)
  slave 1 : S1U = NOR(CLK&M1U, S1L) S1L = NOR(CLK&M1L, S1U, RES)   <- RESPHI0 on the LOWER slave NOR
  n       = NOR(S1L, Q2U)           (lower slave-1 output and the Q2U bus)
  master 2: IU2 = NOR(CLK, ~n)      IL2 = NOR(CLK, n)               (~n from the inverter)
            M2U = NOR(IU2, M2L)     M2L = NOR(IL2, M2U)
  slave 2 : Q2U = NOR(CLK&M2U, Q2L) Q2L = NOR(CLK&M2L, Q2U, RES)   <- RESPHI0 on the LOWER slave NOR
  PP in   = NOR(M1U, Q2U)
"""
import itertools, random, sys

NAMES = ['IU1', 'IL1', 'M1U', 'M1L', 'S1U', 'S1L', 'N', 'NB', 'IU2', 'IL2', 'M2U', 'M2L', 'Q2U', 'Q2L']


def nor(*a):
    return int(not any(a))


def gate(g, s, clk, res):
    if g == 'IU1': return nor(s['Q2U'], clk)
    if g == 'IL1': return nor(s['Q2L'], clk)
    if g == 'M1U': return nor(s['IU1'], s['M1L'])
    if g == 'M1L': return nor(s['IL1'], s['M1U'])
    if g == 'S1U': return nor(clk & s['M1U'], s['S1L'])
    if g == 'S1L': return nor(clk & s['M1L'], s['S1U'], res)
    if g == 'N':   return nor(s['S1L'], s['Q2U'])
    if g == 'NB':  return int(not s['N'])
    if g == 'IU2': return nor(clk, s['NB'])
    if g == 'IL2': return nor(clk, s['N'])
    if g == 'M2U': return nor(s['IU2'], s['M2L'])
    if g == 'M2L': return nor(s['IL2'], s['M2U'])
    if g == 'Q2U': return nor(clk & s['M2U'], s['Q2L'])
    if g == 'Q2L': return nor(clk & s['M2L'], s['Q2U'], res)


def settle(s, clk, res, order, maxit=40):
    """Gauss-Seidel in the given gate order until stable. Returns (converged, flipped-gates)."""
    for _ in range(maxit):
        ch = False
        for g in order:
            v = gate(g, s, clk, res)
            if v != s[g]:
                s[g] = v; ch = True
        if not ch:
            return True
    return False


def init_state(l1t, q1b, m2, q2):
    """Same coordinates as div3_sim.run(): (L1t=M1U, Q1b=S1L, M2=M2L, Q2=Q2U), complementary latches."""
    s = dict(M1U=l1t, M1L=1 - l1t, S1L=q1b, S1U=1 - q1b, M2L=m2, M2U=1 - m2, Q2U=q2, Q2L=1 - q2)
    s['N'] = nor(s['S1L'], s['Q2U']); s['NB'] = 1 - s['N']
    s['IU1'] = s['IL1'] = s['IU2'] = s['IL2'] = 0
    return s


def run(halves, res_set=(), state=(0, 0, 0, 0), order=None, clk0=0, trace=None):
    """One CLK half per step, clk = (t & 1) as in div3_sim (t=0 is CLK=0).
    Returns (pp_out list, nonconverged count)."""
    order = order or NAMES
    s = init_state(*state)
    bad = 0
    out = []
    for t in range(halves):
        clk = t & 1
        res = int(t in res_set)
        if not settle(s, clk, res, order):
            bad += 1
        out.append(nor(s['M1U'], s['Q2U']))
        if trace is not None: trace.append(dict(s, clk=clk, res=res))
    return out, bad


if __name__ == '__main__':
    pass


def run_lag(halves, res_set=(), state=(0, 0, 0, 0), lead=False, order=None):
    """Like run(), but RES edges are applied AFTER the CLK edge has settled (RESPHI0 comes from
    HPHI2, which is clocked by CLK through a flip-flop, a NOR, a NAND and an inverter, so it
    lags the CLK edge by more gates than slave 1's own response). lead=True applies RES first
    (the opposite resolution of the race). Removes the zero-delay race in run()."""
    order = order or NAMES
    s = init_state(*state)
    out, res_prev = [], 0
    for t in range(halves):
        clk = t & 1
        res = int(t in res_set)
        if lead:
            settle(s, 1 - clk, res, order)       # RES changes while the old CLK level still holds
            settle(s, clk, res, order)
        else:
            settle(s, clk, res_prev, order)      # CLK edge first, old RES still applied
            settle(s, clk, res, order)           # then RES changes
        res_prev = res
        out.append(nor(s['M1U'], s['Q2U']))
    return out


def per_line(width=2, lag=True, lead=False, lines=6, line=456):
    """Same sweep as div3_sim.per_line: RESPHI0 once per line, width halves, 12 offsets, 6 states.
    Returns {start CLK level: (min, max Phi0 segment in halves after line 1)}."""
    res = {}
    for off in range(12):
        pulses = {l * line + off + i for l in range(lines) for i in range(width)}
        for st in [(0, 0, 0, 0), (1, 1, 1, 1), (0, 1, 0, 1), (1, 0, 1, 0), (0, 0, 1, 0), (1, 0, 0, 1)]:
            o = run_lag(lines * line, pulses, st, lead=lead)[line:]
            segs, n = [], 1
            for a, b in zip(o, o[1:]):
                if a == b: n += 1
                else: segs.append(n); n = 1
            lo, hi = min(segs[1:]), max(segs[1:])
            k = off & 1
            old = res.get(k, (99, 0))
            res[k] = (min(old[0], lo), max(old[1], hi))
    return res
