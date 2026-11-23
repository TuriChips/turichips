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

## 2026-11-16 · Igris
- **Passed:** **chip-8080 released** (#73/#74 signed off by Sai, card live via turichips.github.io#27; 40 pins checked, drawing rendered). Release evidence checked independently: the full 8080EXM, 25/25 PASS, `logs/acc1/8080exm.log` byte-identical to CI run 43840440461's artifact, and `check_log.py` re-run by me → PASS (chip-8080#72). The first nightly's failure was diagnosed (24/25, `<inr,dcr> a`), and the root cause was our BDOS stub's word at 0006h (Zura), spec gap fixed in chip-8080#69. Post-release history audit of chip-8080: clean (#14). 6502 spec v0 opened (turichips#32), with §10 checks from page images: JMP ($xxFF) wrap (Programming Manual p.141), interrupt/BRK sequence and BRK sets I (pp.131, 144), reset sequence (pp.125–127), I/D rules (pp.26–27), RDY (Hardware Manual p.37).
- **In progress:** transcribing Hardware Manual Appendix A into 6502 spec §4.
- **Blocked:** turichips#32 needs Sai's decision on decimal-mode N/V/Z (three options in §6).

## 2026-11-17 · Igris
- **Passed:** chip-6502 acceptance tests reproduced on the RTL myself: Dormann functional, success trap 3469h at 96,241,375 clocks, 0 bus conflicts (#41); Clark decimal with all five checks, PASS at 53,954,357 clocks (#57); demo log byte-identical at 1beacac (#56). Ran Beru's directed NMI regression on #43: 8/8 PASS. Spec decisions merged after Sai's sign-off: taken-branch dummy reads (#21, 80,000 SST branch vectors, 0 differences per Beru), interrupt poll rule (#27, answers #25), reset comparison + RDY in reset (#30, answers #29/#40), decode contract (#39). Merged the full m6502 (#10, #16, #22–#24, #26, #28, #33, #43), C8 in CI (#38, #53), synthesis (#45, #55) and C1–C7 (#12), all with green CI.
- **In progress:** 6502 release: C1–C7 are on main but not in CI (#58, Titus); gate-level C8 (#50, review:titus); Homer's decimal evidence log, README and STORY (#8).
- **Blocked:** nothing for Sai. TuriChips/.github#1 (my org README) waits for Homer to merge (review:homer added).

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
