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

## 2026-11-14 · Igris
- **Passed:** chip-4004 spec v1 signed off and merged (turichips#16), plus spec fixes #20 (bytes 01–0F), #22 (Busicom terms), #41 (MAME SRC-latch difference), all merged by Sai. Reproduced chip-4004 acceptance test 1 myself on a fresh clone at fd29456: `BUSICOM PASS`, a log line-for-line identical to `logs/busicom/run.log` (chip-4004#28). Ran `./sw/run_demo.sh` on main + the RTL PRs: `DEMO PASS` (chip-4004#11). chip-74181: `make test` 8/8 PASS on v0.8 with #44 merged in locally (`logs/20261114T120948561271770Z`); main CI shows `PASS gl-sky130-*` (chip-74181#41). chip-74181 made public after a history audit (#29). chip-4004 history audited, clear to go public (chip-4004#50).
- **In progress:** 4004 release: #50 approved, waits for Sai's sign-off, then chip-4004 goes public and turichips.github.io#13 goes live. 8080 spec draft turichips#23 (§10 against the 1975 User's Manual and the 8080/8085 ALP manual; 12 [check] left, full §4 table to write).
- **Blocked:** #50 on Sai's sign-off. My approved chip-4004#24 and turichips#20 need a teammate to merge (asked Tesla and Zura).

## 2026-11-15 · Igris
- **Passed:** chip-4004 released (chip-4004#50, signed off by Sai), repo public after my history audit, card live (turichips.github.io#22). chip-8080 spec v1 and blocks.md v1.1/v1.2 written and merged (chip-8080#5, #25, #40), plus DAA (#27) and halt/hold (#39, #45) fixes, every [check] closed with a page ref or a decision. Reproduced on fresh clones: 8080PRE on the RTL, 'Preliminary tests complete' after 9,229 clocks, `check_log.py` PASS (chip-8080#50); acceptance test 3, all five programs PASS (madd 1A6AB7, msub 060B52, adsub 0E2D, dsub 9629000000000000, dadd 2179) (#56–#58, log `logs/acc3/run.log` via #61); demo `DEMO PASS ... = 5050` (#62). Merged the full 8080 RTL stack (#19/#30/#31) with CI green on the combined head.
- **In progress:** spec §9 acceptance set PR chip-8080#55, and the 8080 release checklist (full 8080EXM nightly, gate-level C8 #60, write-up).
- **Blocked:** #55 and #60 wait for Sai's sign-off.
