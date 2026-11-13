# Roadmap

Status: **draft.** Order and dates are proposals, to be confirmed by the manager. Chip details live in `docs/chip-catalog.md`.

The lab runs in two phases:
1. **Phase 1: Historic rebuilds.** Rebuild real chips in the order history made them, to learn what each generation learned.
2. **Phase 2: Our own designs, in families.** A block library, plus families of chips built from it, each with its own targets.

Rule: a chip starts only when the one before it in its stage is released, or the manager says otherwise.

---

## Phase 0: Setup (Nov–Dec 2026)
| # | Item | Why |
|---|------|-----|
| 0.1 | Toolchain: Verilator, Yosys, OpenROAD, one-command build and test, CI | Everything else depends on it. |
| 0.2 | **74181 ALU** | A dry run of the full pipeline (spec → RTL → tests → synthesis → write-up) on a tiny chip. |

## Phase 1: Historic rebuilds (Dec 2026 → ~mid 2027)

### Stage 1.1: First CPUs
| # | Chip | Year | Notes |
|---|------|------|-------|
| 1 | Intel 4004 | 1971 | **First card on the website.** |
| 2 | Intel 8080 | 1974 | |
| 3 | MOS 6502 | 1975 | Reused by the Atari 2600, NES and C64. |
| 4 | Zilog Z80 | 1976 | Leads into the Game Boy and Master System. |

### Stage 1.2: First machines (reuse the cores from 1.1)
| # | Machine | Year | Notes |
|---|---------|------|-------|
| 5 | Atari 2600 (TIA + RIOT) | 1977 | First video output. |
| 6 | NES (2A03 + PPU) | 1983 | Homebrew demos. |
| 7 | Game Boy (SM83 + PPU + APU) | 1989 | First full system-on-chip. |

### Stage 1.3: 16/32-bit and RISC
| # | Chip | Year | Notes |
|---|------|------|-------|
| 8 | Motorola 68000 | 1979 | |
| 9 | Berkeley RISC-I | 1982 | Ancestor of RISC-V. |
| 10 | ARM2 | 1986 | |
| 11 | MIPS R2000 | 1986 | 5-stage pipeline. **Direct prep for R3.** |

### Stage 1.4: Graphics
| # | Chip | Year | Notes |
|---|------|------|-------|
| 12 | NEC µPD7220 | 1982 | 2D drawing in hardware. |
| 13 | PlayStation GTE + GPU | 1994 | First 3D. |
| 14 | 3dfx Voodoo Graphics | 1996 | Texture-mapped 3D. |

### Stage 1.5: Bridges to Phase 2
| # | Chip | Year | Notes |
|---|------|------|-------|
| 15 | TI TMS32010 DSP | 1983 | Multiply-accumulate: the bridge to ML. |
| 16 | Systolic array (H.T. Kung) | 1978–82 | Core of the M family. |
| 17 | MIPS R10000 (simplified) | 1996 | Out-of-order. **Direct prep for R5.** |

Optional, if time allows: Z80 → Sega Master System, ARM7TDMI → Game Boy Advance, 8087 floating point, Pentium.

## Phase 2: Our own designs, in families (~mid 2027 → Nov 2027)

From here the lab designs its own chips. Each family shares an instruction set and blocks from the library. Each family member has its own speed, size and power targets.

### Block library
- Versioned blocks (cores, caches, bus, memory controller, peripherals), each with its own test suite.
- One shared bus standard across all blocks.
- When a block changes, the tests of every chip that uses it run again.
- A block enters the library only after the team has built something like it two or three times. No platform before it has earned it.

### R family: RISC-V CPUs (main year goal)
Final name TBD.

| Member | What it is | Must pass |
|--------|------------|-----------|
| R1 | Small RV32I microcontroller, single-cycle or 3-stage | riscv-tests (RV32I) |
| R3 | 5-stage pipeline with caches | riscv-tests + benchmarks (e.g. CoreMark) |
| R5 | RV64 with memory management, out-of-order | riscv-tests + **boots Linux in simulation** |

### M family: ML accelerators (bigger vision)
| Member | What it is | Target |
|--------|------------|--------|
| M1 | 8×8 int8 systolic array + R1 as the control core | Runs a small model end to end (e.g. MNIST) |
| M2 | 32×32 + on-chip buffers | Bigger models; size and speed numbers on SkyWater 130nm |
| M3 | 128×128, TPU-v1 style | Full report on size, speed and power |

### New roles for Phase 2
- **Platform Architect:** owns the block library, its interfaces and its versions.
- **Product Manager:** sets each family member's targets and decides what the next member adds.

## KPIs by phase
- **Phase 1:** chips released, times agents asked the manager to step in, days from spec to release.
- **Phase 2:** the same, plus the share of each new chip built from library blocks, and family targets met.
