# Standup log

Format: `agents/_rules.md` → Standup format. Append, newest at the bottom.

## 2026-11-13 · Beru
- **Passed:** chip-74181 exhaustive check (16,384 cases, 0 mismatches, 0 X/Z, Verilator + Icarus) and B7 cascade (4,194,304 cases, 0 mismatches) on main @56390eb. Logs: chip-74181 `logs/random/main-56390eb/` (PR #18). Ref model self-test: 0 mismatches. Mutation run on Titus's suite: 11/12 caught. The miss (B8 X/Z) is fixed in chip-74181#14, verified on #15.
- **In progress:** chip-74181#18 (evidence logs, review:titus); re-reviewing toolchain#11 (pin check, false mismatch when two tags share a commit) once Tesla updates it.
- **Blocked:** nothing.

## 2026-11-14 · Beru
- **Passed:** chip-4004 C9 on main's RTL, 10,000 programs × 1,000 cycles, every pin every period, 0 mismatches (chip-4004 `logs/c9-full-20261114T*/SUMMARY.md`, #21 merged). C9 on Leo's sky130 gate-level i4004 netlist, 1,000 × 1,000, 0 mismatches, plus demo and Busicom PASS on the netlist (`logs/c9-gl-sky130-20261114T143628Z/`, #34). Acceptance test 3, MAME mcs40 vs model, 40 × 3,000 all agree (`logs/acc3-*`, #30), and the same programs on the RTL, 0 mismatches. CI on a GitHub runner: PASS ref-selftest / c9 / acc3 (chip-4004 run 43604539922). chip-74181 sky130 gate-level checks PASS in CI (run on #41).
- **In progress:** chip-4004#30 (acceptance test 3, last piece of #7) and #34 (gate-level evidence, closes #33).
- **Blocked:** #30 waits on Titus's review (review:titus since the morning), #34 on Leo's (review:leo). Nothing else.
