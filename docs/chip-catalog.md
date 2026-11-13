# Chip Catalog: candidates up to the early 2000s

Status: **draft for selection.** Mark `x` in the Pick column, then we turn the picks into `docs/roadmap.md`.

Transistor counts are approximate and are only there to show scale. The Architect verifies every fact against datasheets before writing a spec.

Difficulty: 1 = a weekend for the team · 5 = a multi-week milestone.

## Track 0: Building blocks (warm-ups, to test the whole pipeline)

| Pick | Chip | Year | Size | Why it matters | Diff |
|---|---|---|---|---|---|
| [ ] | 7400-series logic (gates, flip-flops, counters) | 1964+ | tens of transistors | The parts everything else is made from. Good for a first dry run of the toolchain. | 1 |
| [ ] | 74181 4-bit ALU | 1970 | ~75 gates | First complete ALU on one chip. Small, exact truth tables, easy to test. | 1 |
| [ ] | Intel 8087 floating-point coprocessor | 1980 | ~45,000 | Floating point done right. Needed later for GPUs and ML. | 4 |
| [ ] | TI TMS32010 DSP | 1983 | ~55,000 | Hardware multiply-accumulate in one cycle: the ancestor of ML accelerators. | 3 |

## Track 1: CPUs

| Pick | Chip | Year | Size | Why it matters / used in | Diff |
|---|---|---|---|---|---|
| [ ] | Intel 4004 | 1971 | ~2,300 | First commercial microprocessor. 4-bit. | 2 |
| [ ] | Intel 8008 | 1972 | ~3,500 | First 8-bit CPU. | 2 |
| [ ] | Intel 8080 | 1974 | ~4,500 | Altair; ancestor of the x86 line. | 2 |
| [ ] | Motorola 6800 | 1974 | ~4,100 | Clean 8-bit design; led to the 6502. | 2 |
| [ ] | MOS 6502 | 1975 | ~3,500 | Apple II, C64, NES, Atari 2600. Highest reuse in Track 2. | 2 |
| [ ] | Zilog Z80 | 1976 | ~8,500 | ZX Spectrum, Master System, Game Boy-like core. | 3 |
| [ ] | Intel 8086 | 1978 | ~29,000 | 16-bit; the root of x86. | 3 |
| [ ] | Motorola 68000 | 1979 | ~68,000 | Mac, Amiga, Sega Genesis. 32-bit inside. | 4 |
| [ ] | Berkeley RISC-I | 1982 | ~44,000 | First RISC; a direct ancestor of RISC-V. | 3 |
| [ ] | Intel 80286 | 1982 | ~134,000 | Protected mode, memory protection. | 4 |
| [ ] | ARM1 / ARM2 | 1985/86 | ~25,000 / ~30,000 | Tiny, elegant 32-bit RISC. | 3 |
| [ ] | Intel 80386 | 1985 | ~275,000 | 32-bit with paging: first CPU that could run a modern OS. | 5 |
| [ ] | MIPS R2000 / R3000 | 1986/88 | ~110,000 | The textbook 5-stage pipeline. R3000 is in the PlayStation. | 3 |
| [ ] | Intel 80486 | 1989 | ~1.2M | Pipelined x86 with on-chip cache and FPU. | 5 |
| [ ] | Intel Pentium (P5) | 1993 | ~3.1M | Superscalar: two instructions per clock. | 5 |
| [ ] | ARM7TDMI | 1994 | ~75,000 | Game Boy Advance, early phones. Thumb instructions. | 3 |
| [ ] | Intel Pentium Pro (P6) | 1995 | ~5.5M | Out-of-order execution goes mainstream. | 5 |
| [ ] | MIPS R10000 | 1996 | ~6.8M | Clean out-of-order design. **Closest blueprint for our out-of-order RISC-V goal.** | 5 |
| [ ] | DEC Alpha 21264 | 1998 | ~15M | The best out-of-order design of the era. Study it more than rebuild it. | 5 |

## Track 2: Retro machines (the custom chips inside them)

| Pick | Machine | Year | Chips to build | Why it matters | Diff |
|---|---|---|---|---|---|
| [ ] | Atari Pong (arcade) | 1972 | Discrete logic board, not a CPU | Fun first demo, but it's a board, not a chip. | 2 |
| [ ] | Atari 2600 | 1977 | 6507 (6502 variant), TIA video/sound, RIOT | Draws the screen in real time, one line at a time. | 3 |
| [ ] | Apple II | 1977 | 6502 + video timing logic | Mostly glue logic. Good systems practice. | 2 |
| [ ] | TMS9918 video chip (MSX, ColecoVision) | 1979 | Video display processor | First tile/sprite video chip; the Master System's video chip extends it. | 3 |
| [ ] | ZX Spectrum | 1982 | Z80 + ULA | One small custom chip; easy full machine. | 2 |
| [ ] | Commodore 64 | 1982 | 6510, VIC-II video, SID sound | Famous video and sound chips. | 4 |
| [ ] | NES | 1983 | Ricoh 2A03 (6502 + sound), 2C02 PPU | Huge homebrew library for demos. | 4 |
| [ ] | Amiga | 1985 | Agnus, Denise, Paula | Custom chips for graphics, sound and DMA. | 5 |
| [ ] | Sega Master System | 1985 | Z80 + VDP + SN76489 sound | Builds on Z80 + TMS9918. | 3 |
| [ ] | Sega Genesis | 1988 | 68000 + Z80 + VDP + YM2612 FM sound | First two-CPU system. | 5 |
| [ ] | Game Boy | 1989 | SM83 CPU + PPU + APU on one chip | Very well documented, great test programs. A strong early system-on-chip. | 3 |
| [ ] | SNES | 1990 | 65C816, PPU1/2, SPC700 sound | Complex video modes. | 5 |
| [ ] | PlayStation | 1994 | R3000A + GTE (3D math) + GPU | Bridge into 3D graphics. | 5 |
| [ ] | Nintendo 64 | 1996 | VR4300 + RCP (RSP + RDP) | Very hard. Optional stretch goal. | 5 |
| [ ] | Game Boy Advance | 2001 | ARM7TDMI + PPU | Builds on ARM7 and the Game Boy. | 4 |

## Track 3: Graphics

| Pick | Chip | Year | Why it matters | Diff |
|---|---|---|---|---|
| [ ] | NEC µPD7220 | 1982 | First graphics display processor: lines, arcs and fills in hardware. | 3 |
| [ ] | IBM VGA | 1987 | The standard PC display controller. | 3 |
| [ ] | PlayStation GTE + GPU | 1994 | Fixed-point 3D maths + triangle drawing. | 4 |
| [ ] | 3dfx Voodoo Graphics | 1996 | Texture-mapped 3D in hardware. The classic first 3D accelerator. | 5 |
| [ ] | Nvidia GeForce 256 | 1999 | "First GPU": transform and lighting on the chip. Too large to rebuild whole, so build a subset. | 5 |
| [ ] | GeForce3-style programmable shader | 2001 | Programmable pixel and vertex units: the step toward GPU computing. | 5 |

## Track 4: ML (mostly after 2000; the long-term vision)

| Pick | Design | Year | Why it matters | Diff |
|---|---|---|---|---|
| [ ] | Systolic array (H.T. Kung) | 1978–82 | The core idea behind TPUs. Small and testable. | 2 |
| [ ] | Intel ETANN 80170 | 1989 | Early neural-network chip. Analog, so study only, not a rebuild. | n/a |
| [ ] | Google TPU v1 (subset) | 2016 | int8 systolic matrix unit for inference. | 5 |
| [ ] | MIT Eyeriss | 2016 | Energy-efficient convolution dataflow. | 5 |
| [ ] | NVIDIA NVDLA | 2017 | Fully open-source accelerator; a reference point to measure against. | 5 |

## Finish lines (from COMPANY.md)

- **Main year goal: RISC-V CPU.** Step up as RV32I single-cycle → 5-stage pipeline → caches → RV64 with memory management, booting Linux → out-of-order. Must pass the official RISC-V test suite (riscv-tests) at every step.
- **Bigger vision: ML accelerator.** Systolic-array inference engine with a RISC-V control core, real size and speed numbers on an open process (SkyWater 130nm).
