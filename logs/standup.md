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

## 2026-11-18 · Igris
- **Passed:** 6502 released and public (chip-6502#65, Sai's sign-off, after my history audit: no third-party files, no secrets). Merged with green CI after reviewing:
  - C1–C7 in CI (#59, #61), gate-level C8 (#50), final C8 (#62);
  - README (#64, corrected from my review), STORY (#66, #67), demo and decimal logs (#56, #60), reproduced byte-identical by me;
  - website card turichips.github.io#30, all 40 pins checked against Hardware Manual Figure 1.15.
  
  Z80 (chip #4) spec draft turichips#37, from Zilog's 1977/78 manuals plus Mostek's MK78515 and MK3880:
  - half-T-state pin tables for every bus cycle;
  - 698 documented opcodes;
  - all 11 instruction groups with cycle types;
  - flags, interrupts, reset, C1–C8;
  - zexdoc licence checked (GPL v2+).
- **In progress:** turichips#37 waits for Beru's and Zura's review, then Sai's decisions (§3 summary: Mostek for the flags zexdoc checks, MK3880 for per-cycle bus types). Then `blocks.md` code tables.
- **Blocked:** chip-6502#69 (pinout) and turichips#37 need Sai's sign-off. Reviews on #37 have been pending since 09:53 UTC.

## 2026-11-19 · Igris
- **Passed:** answered all 16 items of Beru's model-builder review of the Z80 spec (turichips#37). Beru re-reviewed and **approved the content** (08:23 UTC). New from sources:
  - DAA table (PM p.132, the same as Mostek's);
  - block I/O A8–A15 from Zilog's 1994 User's Manual (output shows B−1, input shows B);
  - signed d and JR offset (PM pp.30, 223).
  
  New proposed Decisions: F[5:3], R, HALT (§6.3), and sampling points, instruction boundaries and stimulus (§8.4).
- **In progress:** turichips#37 waits for Zura's timing review. Then `blocks.md` code tables.
- **Blocked:** Sai's decisions 6–8 on turichips#37 (Mostek MK78515 for the flags zexdoc checks; Mostek MK3880 for per-cycle bus types; DAA outside PM's table, and H) and sign-off. chip-6502#69 (pinout) also waits for Sai.

## 2026-11-20 · Igris
- **Passed:** nothing new; no PRs needed review or merging.
- **In progress:** turichips#37, the Z80 spec, approved on content by Beru. It still waits for Zura's timing review (`review:zura`, no activity since 2026-11-18).
- **Blocked:** Sai's decisions 6–8 and sign-off on turichips#37. chip-6502#69 (pinout) is also waiting for Sai.

## 2026-11-21 · Igris
- **Passed:** nothing new; nothing in my queue to review or merge.
- **In progress:** turichips#37 (Z80 spec): approved on content by Beru; Zura's timing review is still pending.
- **Blocked:** Sai's decisions 6–8 and sign-off on turichips#37, and Sai's sign-off on chip-6502#69. No team activity since 2026-11-19 09:24 UTC.

## 2026-11-22 · Igris
- **Passed:** nothing new; my queue had no reviews or merges.
- **In progress:** turichips#37, the Z80 spec. It's unchanged since 2026-11-19: approved on content by Beru, and Zura's review is pending.
- **Blocked:** Sai's decisions 6–8 and sign-off on turichips#37, and Sai's sign-off on chip-6502#69.
