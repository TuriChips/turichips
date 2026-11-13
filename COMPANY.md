# Turichips: Company Document

_Last updated: 2026-11-13 · Owner: Sai (manager)_

> Every agent reads this first, every session. If something here conflicts with your job description, this document wins. Ask the manager.

## 1. Who we are
Turichips is the world's first chip lab run by AI. A team of AI agents designs, verifies and documents chips end to end. One human manager sets direction and merges pull requests. Everything else is done by the agents.

We only design. Everything happens in software: RTL, simulation, testbenches, synthesis and open-source layout. We never deal with manufacturing.

## 2. Mission
Build the first chip design lab that runs on its own, and within one year design a modern chip with nothing but agents.

## 3. What we are building
We rebuild real chips in the order history built them. Each chip teaches the team what the next one needs, and together they build up the intuition a human chip team gains over decades.

**Tracks**, roughly in order:
1. **CPUs.** Early microprocessors from the 1970s and 80s, then moving up the ladder.
2. **Retro machines.** The chips inside classic consoles and computers (e.g. Atari, NES, Sega Master System and Genesis, Game Boy).
3. **Graphics chips.**
4. **ML chips.**

**How the lab runs: two phases.** Full detail in `docs/roadmap.md`.
- **Phase 1: Historic rebuilds.** Real chips, rebuilt in historical order across the four tracks.
- **Phase 2: Our own designs, in families.** The same pattern big labs use: a library of reusable, tested blocks, and families of chips built from it. Each family member has its own speed, size and power targets, and a new chip is mostly existing blocks plus one or two new ones.
  - **R family:** RISC-V CPUs. R1 microcontroller → R3 pipelined with caches → R5 out-of-order, Linux-capable.
  - **M family:** ML accelerators. Systolic arrays at growing sizes, with R1 as the control core.
  - New roles for Phase 2: Platform Architect (owns the block library) and Product Manager (sets family targets).

**The order of chips is a draft** until the manager confirms `docs/roadmap.md`. Do not start a chip that is not listed in the roadmap.
- Candidates: `docs/chip-catalog.md`
- Roadmap: `docs/roadmap.md` (draft)
- **Current chip:** TODO

**What "done" means for one chip:**
- Verilog (or the stack the spec names) for the full chip, in simulation only.
- A proper testbench, plus the acceptance tests named in the spec, all passing, with logs as evidence.
- A synthesis report: size and speed. For milestone chips, an open-source layout too.
- A demo running on the simulated chip.
- A public write-up in `docs/release.md`.

**Public output:** the lab website at TODO (e.g. `turichips.com` or `chips.turilabs.in`, domain not bought yet).
- The homepage reads "The world's first chip lab run by AI", with one card per chip below it.
- Each card shows an image of the chip made by the team itself, ideally a render of our own layout. Clicking the card opens that chip's write-up.
- The first card is the first chip we build.

## 4. Plan

### Year goal (by 2026-11-13 → 2027-11)
Go from rebuilding the earliest chips to designing a modern chip with agents only.
- **Main finish line: a RISC-V CPU** designed entirely by agents. Built up step by step to an out-of-order core that passes the official RISC-V test suite (riscv-tests) and boots Linux in simulation.
- **Bigger vision: an ML accelerator.** A systolic-array inference chip with real size and speed numbers on an open process (e.g. SkyWater 130nm).
- Candidate chips for the ladder are in `docs/chip-catalog.md`.

### Q4 2026 (now → end of December)
| # | Goal | Owner role | Due | Status |
|---|------|------------|-----|--------|
| 1 | Toolchain works: one command builds, simulates, tests and synthesizes | Infrastructure | TODO | not started |
| 2 | Roadmap confirmed (draft exists in docs/roadmap.md) | Manager + Architect | TODO | draft |
| 3 | 74181 dry run, then Chip #1 (Intel 4004) released end to end (spec → RTL → tests → synthesis → demo → write-up) | Everyone | TODO | not started |
| 4 | Lab website live with chip #1's card | Software and Docs | TODO | not started |

### Q1 2027
TODO, set at the end of Q4. Rough intent: finish the early-CPU part of the ladder and start the retro machines track.

## 5. KPIs
Every number needs a source: a log, a report or a script.

| KPI | Target | Current | Source |
|-----|--------|---------|--------|
| Chips released | Q4: 1 (4004) | 0 | docs/release.md per chip |
| Spec behaviours with ≥1 test (current chip) | 100% | n/a | tests/ coverage list |
| Acceptance tests passing (current chip) | all | n/a | logs/ |
| Random-test differences vs reference model | 0 | n/a | tests/random/ |
| Bugs found by verification before release | tracked | n/a | GitHub issues |
| **Times agents asked the manager to step in, per chip** | trending to 0 | n/a | issues labelled `needs-manager` |
| Days from spec to release, per chip | trending down | n/a | issues + release dates |
| Share of each new chip built from library blocks (Phase 2) | rising | n/a | block library manifest |

Times agents asked the manager to step in is the number that measures the mission. If it doesn't go down from one chip to the next, the lab is not learning.

## 6. This week's focus
Week of 2026-11-13: set up the repo, the toolchain and the agent start-up scripts. Agree the roadmap.

## 7. Team
| Name | Role | Agent file | Owns |
|------|------|------------|------|
| Sai | Manager (human) | none | direction, this document, merges all PRs |
| Vera | Architect | agents/architect.md | docs/spec.md, docs/blocks.md |
| Theo | Designer A (control side) | agents/designer-a.md | rtl/control/, rtl/top.v |
| Mira | Designer B (data side) | agents/designer-b.md | rtl/datapath/ |
| Quinn | Verification Engineer A (test builder) | agents/verification-a.md | tb/, tests/ |
| Rook | Verification Engineer B (breaker) | agents/verification-b.md | ref/, tests/random/ |
| Otto | Infrastructure Engineer | agents/infrastructure.md | scripts/, Makefile, .github/ |
| Petra | Physical Design Engineer | agents/physical-design.md | synth/ |
| Juno | Software and Docs Engineer | agents/software-docs.md | sw/, README.md, docs/release.md |

## 8. Meetings and reporting
- **Standup:** TODO (days and time). Each agent appends to `logs/standup.md` (format in `agents/_rules.md`).
- **Weekly review:** TODO (day and time). What shipped, what slipped, and what could have been done better. Lessons go into each agent's memory.

## 9. Decisions log
Append-only. Date, decision, why.
- 2026-11-13: Company founded as Turichips. Eight roles defined.
- 2026-11-13: Finish lines set: main goal is a RISC-V CPU, bigger vision is an ML accelerator. Verilator for simulation, no FPGA.
- 2026-11-13: Agents named, each with a personality: Vera, Theo, Mira, Quinn, Rook, Otto, Petra, Juno.
- 2026-11-13: Two phases: historic rebuilds first, then our own designs in families (R family = RISC-V, M family = ML) built from a shared block library.
- 2026-11-13: Simulation only, no manufacturing. Chips are rebuilt in historical order across four tracks: CPUs → retro machines → graphics → ML.
