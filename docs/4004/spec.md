# Spec: Intel 4004 (Chip #1), DRAFT

Status: **DRAFT v0, not normative.** Written by Vera on 2026-11-13 so the spec is reviewed by the time the 74181 is released. Nobody builds from this until (a) the 74181 is released (roadmap rule), (b) every box in §10 is ticked against the datasheet, and (c) Sai signs it off. It then moves to `TuriChips/chip-4004`, the same way the 74181 spec did (#6).

Sources, to be checked in §10:
- Intel, *MCS-4 Micro Computer Set Users Manual*, Rev. 4, February 1973 (instruction set, timing, 4001/4002).
- Intel, *4004 Single Chip 4-Bit P-Channel Microprocessor* datasheet (pins, timing diagram).

Anything below marked **[check]** comes from memory of those documents and must be confirmed against the page before this spec is normative.

## 1. Scope
- The **4004 CPU**, cycle-accurate at its 16 pins: every clock phase, the value on `d[3:0]`, `sync`, `cm_rom` and `cm_ram[3:0]` is specified (§4).
- The **4001 ROM** (256 × 8 + 4-bit I/O port) and the **4002 RAM** (4 registers × (16 + 4) × 4 bits + 4-bit output port) as companion blocks. A 4004 can't fetch an instruction without them, and the acceptance tests and demo run on an MCS-4 system. They are in scope as RTL, at reduced detail: §7.
- Out of scope: the 4003 shift register, electrical behaviour (p-channel levels, two-phase non-overlap times), the 4008/4009 adapters, and the 4040.
- Logic convention: **positive logic, 1 = true**, everywhere in this spec and the RTL. The real chip is negative-logic PMOS (a 1 on the bus is the more negative voltage). We model logic values only. This is the same choice as the 74181's active-high data.
- Clock: one rising-edge clock `clk` stands in for the two-phase φ1/φ2. One `clk` period = one of the 8 clock periods of an instruction cycle (§4). Real timing (8 clock periods per cycle, 10.8 µs per instruction cycle, Users Manual p.6 and p.28) is noted, not modelled.

## 2. Pins (top module `i4004`)
| Signal | Dir | Width | Meaning | Real pin **[check]** |
|--------|-----|-------|---------|----------|
| `clk` | in | 1 | Model clock, one per clock period | φ1 6, φ2 7 |
| `reset` | in | 1 | Synchronous reset, active high (§5) | 9 |
| `test` | in | 1 | TEST input, read by JCN (§6.2) | 10 (confirmed, manual p.32) |
| `d_in[3:0]` | in | 4 | Data bus, value driven by ROM/RAM | 1–4 (D0–D3) |
| `d_out[3:0]` | out | 4 | Data bus, value driven by the 4004 | 1–4 |
| `d_oe` | out | 1 | 1 when the 4004 drives the bus | n/a |
| `sync` | out | 1 | SYNC: 1 during X3, marks the start of the next instruction cycle | 8 (confirmed, manual p.86) |
| `cm_rom` | out | 1 | CM-ROM | 11 |
| `cm_ram[3:0]` | out | 4 | CM-RAM0..3 | 16, 15, 14, 13 |

The real bidirectional bus is split into `d_in`, `d_out` and `d_oe` so the RTL has no tri-states. The system top (§7) resolves it as `bus = d_oe ? d_out : (any ROM/RAM driving ? its value : 4'b0000)`. A cycle where two drivers are on at once is a bug, and the tests must flag it.

## 3. Programmer's model
| Name | Width | Reset value | Notes |
|------|-------|-------------|-------|
| `acc` | 4 | 0 | Accumulator |
| `cy` | 1 | 0 | Carry/link |
| `r[0..15]` | 16 × 4 | 0, only if reset is held ≥ 64 clocks (§5) | Index registers. Pair `P0..P7` = `{r[2p], r[2p+1]}`, with `r[2p]` the **high** nibble |
| `pc` | 12 | 0 | Program counter (stack level 0) |
| `stack[1..3]` | 3 × 12 | 0 | Return addresses. JMS pushes, BBL pops. A 4th JMS loses the deepest (first-stored) return address (manual p.13) |
| `src_addr` | 8 | 0 | Last value sent by SRC (chip/register/character select for I/O and RAM instructions) |
| `ram_bank` | 3 | 0 | Set by DCL, selects which CM-RAM line(s) are active (§6.5) |

Address space: 4096 bytes of ROM (16 × 4001), in 16 pages of 256. Every instruction is 1 or 2 bytes (words). A 2-word instruction takes 2 instruction cycles.

## 4. Instruction cycle timing (normative)
One instruction cycle = 8 clock periods, in this order:

| Period | Name | Bus (`d`) carries | Driver | `cm_rom` | `cm_ram` | `sync` |
|--------|------|-------------------|--------|----------|----------|--------|
| 0 | A1 | `pc[3:0]` | 4004 | 0 | 0 | 0 |
| 1 | A2 | `pc[7:4]` | 4004 | 0 | 0 | 0 |
| 2 | A3 | `pc[11:8]` | 4004 | 1 | selected bank(s); meaningless to RAMs (manual p.15) | 0 |
| 3 | M1 | OPR (high nibble of the instruction byte) | ROM | 0 | 0 | 0 |
| 4 | M2 | OPA (low nibble) | ROM | 1 if I/O-group (OPR = 1110), else 0 | selected bank(s) if I/O-group, else 0 | 0 |
| 5 | X1 | instruction dependent (§6) | §6 | 0 | 0 | 0 |
| 6 | X2 | SRC: `src_addr[7:4]` from the pair; I/O read: data in; I/O write: `acc` out | §6 | 1 if SRC | selected bank(s) if SRC | 0 |
| 7 | X3 | SRC: `src_addr[3:0]` | §6 | 0 | 0 | **1** |

- `pc` increments once per word fetched, after M2. When exactly it updates is not visible at the pins except through A1–A3, so any internal choice that gives the right A1–A3 values is allowed.
- After `reset` goes low, the first clock period is A1 of a cycle fetching address 0x000.
- Only the bus values in A1–A3, X2 and X3, and the `cm_*`/`sync` lines, are pin-visible requirements. The RTL may do anything internally during M1/M2/X1 as long as the pins match.

## 5. Reset
Manual p.10: during reset all static flip-flops are cleared, the data bus is 0, timing starts from step 0 and CM-RAM0 is selected. The index registers are dynamic and are cleared only if RESET is held for **at least 8 instruction cycles (64 clock periods)**, so the refresh counter scans all of them.

Our model: while `reset` = 1 on a rising `clk` edge, `acc`, `cy`, `pc`, the stack, `src_addr`, `ram_bank` (0 = CM-RAM0) and the cycle counter (to A1) are cleared. `r[0..15]` must be 0 after `reset` has been 1 for 64 consecutive edges; the RTL may clear them sooner. Tests always hold `reset` for ≥ 64 edges and must not check `r` after a shorter reset.

## 6. Instructions (normative)
46 instructions. `OPR` = high nibble of the first word, `OPA` = low nibble. `R` = `r[OPA]`, `P` = pair `OPA[3:1]`. All arithmetic is mod 16 unless noted.

### 6.1 One-word, 1 cycle
| Hex | Mnemonic | Effect |
|-----|----------|--------|
| 00 | NOP | none |
| 6R | INC R | `R = R + 1`. `cy` unchanged |
| 8R | ADD R | `{cy, acc} = acc + R + cy` |
| 9R | SUB R | `{cy, acc} = acc + ~R + ~cy`. On input, `cy` = 1 means a borrow is pending; on output, `cy` = 1 means *no* borrow. So chained subtraction needs CMC between digits |
| AR | LD R | `acc = R` |
| BR | XCH R | swap `acc` and `R` |
| CD | BBL D | `pc = pop()`, `acc = D` |
| DD | LDM D | `acc = D` |
| 2(2p+1) | SRC Pp | `src_addr = Pp`; drive it on the bus at X2 (high) and X3 (low), with `cm_rom` = 1 and the selected `cm_ram` lines at X2 (§4) |
| 3(2p+1) | JIN Pp | `pc[7:0] = Pp`. `pc[11:8]` = page of the **next** instruction's address, so a JIN at xFF jumps into page x+1 (manual p.30) |

### 6.2 Two-word, 2 cycles
The second word is `B` (8 bits). "Same page" means `pc[11:8]` of the address **after the second word**. So an instruction whose second word sits at the last byte of a page (first word at xFE) jumps within page x+1. This is a known 4004 quirk and is tested.

| Hex | Mnemonic | Effect |
|-----|----------|--------|
| 1C B | JCN C, B | `cond = (C[2] & acc==0) \| (C[1] & cy==1) \| (C[0] & test==0)`; if `cond ^ C[3]`: `pc[7:0] = B` (same page). Manual p.32: `JUMP = ~C1·X + C1·~X`, C1 = `C[3]`, C2 = `C[2]`, C3 = `C[1]`, C4 = `C[0]`. So C = 0000 never jumps and C = 1000 always jumps |
| 2(2p) B | FIM Pp, B | `Pp = B` |
| 3(2p) | FIN Pp | 1 word, **2 cycles**: second cycle fetches ROM byte at `{same page, P0}` into `Pp`. At xFF the byte comes from page x+1 (manual p.31). FIN P0 overwrites the address it used |
| 4A B | JUN | `pc = {A, B}` (12 bits) |
| 5A B | JMS | `push(address after B)`, `pc = {A, B}` |
| 7R B | ISZ R, B | `R = R + 1`; if `R != 0`: `pc[7:0] = B` (same page) |

### 6.3 I/O and RAM group (OPR = 1110), 1 cycle
All act on the chip, register and character selected by the last SRC and by `ram_bank`. M = the selected RAM character, S_n = status character n.

| Hex | Mnemonic | Effect |
|-----|----------|--------|
| E0 | WRM | M = `acc` |
| E1 | WMP | RAM output port = `acc` |
| E2 | WRR | ROM I/O port = `acc` |
| E3 | WPM | Write program RAM (4008/4009 only). **No effect in our system.** Pins as for any I/O-group instruction (§4) |
| E4–E7 | WR0–WR3 | S0–S3 = `acc` |
| E8 | SBM | `{cy, acc} = acc + ~M + ~cy` |
| E9 | RDM | `acc = M` |
| EA | RDR | `acc` = ROM I/O port |
| EB | ADM | `{cy, acc} = acc + M + cy` |
| EC–EF | RD0–RD3 | `acc` = S0–S3 |

### 6.4 Accumulator group (OPR = 1111), 1 cycle
| Hex | Mnemonic | Effect |
|-----|----------|--------|
| F0 | CLB | `acc = 0`, `cy = 0` |
| F1 | CLC | `cy = 0` |
| F2 | IAC | `{cy, acc} = acc + 1` |
| F3 | CMC | `cy = ~cy` |
| F4 | CMA | `acc = ~acc` |
| F5 | RAL | `{cy, acc} = {acc, cy}` (rotate left through carry) |
| F6 | RAR | `{acc, cy} = {cy, acc}` (rotate right through carry) |
| F7 | TCC | `acc = {3'b0, cy}`, `cy = 0` |
| F8 | DAC | `{cy, acc} = acc + 4'b1111`, so `cy` = 0 exactly when `acc` was 0 (borrow) |
| F9 | TCS | `acc = cy ? 10 : 9`, `cy = 0` |
| FA | STC | `cy = 1` |
| FB | DAA | if `cy` or `acc > 9`: `acc = acc + 6`, and `cy = 1` if that addition carries out; otherwise `cy` unchanged |
| FC | KBP | `acc` = 0→0, 1→1, 2→2, 4→3, 8→4, anything else → 15 |
| FD | DCL | `ram_bank = acc[2:0]` (§6.5) |
| FE, FF | (none) | Not instructions. **Decision: execute as NOP.** Tests must not depend on it |

### 6.5 RAM bank selection (DCL)
| `ram_bank` | Active line(s) |
|------------|----------------|
| 000 | CM-RAM0 |
| 001 | CM-RAM1 |
| 010 | CM-RAM2 |
| 011 | CM-RAM1, CM-RAM2 |
| 100 | CM-RAM3 |
| 101 | CM-RAM1, CM-RAM3 |
| 110 | CM-RAM2, CM-RAM3 |
| 111 | CM-RAM1, CM-RAM2, CM-RAM3 |
Structure confirmed (manual p.36: three accumulator bits, 8 codes, 000 = CM-RAM0 only); the scan's table is partly unreadable in OCR, so the row-by-row mapping is still to be read off the page image.

## 7. System: 4001 and 4002 (reduced detail)
- `i4001` ROM: 256 × 8 contents from a `$readmemh` file, chip number 0–15 (strap), 4-bit I/O port configured as all-output or all-input per chip (metal-mask option, here a parameter). It responds to A1–A3 with its chip number on A3 + `cm_rom`, and drives OPR/OPA at M1/M2. SRC's high nibble at X2 with `cm_rom` selects the chip for WRR/RDR.
- `i4002` RAM: 4 registers × 16 data characters + 4 status characters, 4 bits each; 4-bit output port. Chip select = `src_addr[7:6]`, register = `src_addr[5:4]` (manual p.15), with the chip number within a bank set by the 4002-1/-2 variant and its P0 pin **[check: strap mapping]**, character = `src_addr[3:0]`, bank = which `cm_ram` line it is on.
- `mcs4_system`: one 4004, up to 16 4001s, up to 16 4002s (4 per bank × 4 banks). The default build for tests is 1 × 4001 per program page used, 4 × 4002 on bank 0.

## 8. Behaviours to test
| ID | Behaviour |
|----|-----------|
| C1 | Each of the 46 instructions gives exactly the §6 result on `acc`, `cy`, registers, `pc`, stack, RAM and ports, including the `cy` cases of ADD/SUB/ADM/SBM/IAC/DAC/DAA |
| C2 | Pin timing: for every instruction class, `d_out`/`d_oe`, `sync`, `cm_rom`, `cm_ram` per period match §4 |
| C3 | Page quirk: JCN, ISZ, FIN and JIN with the second word (or next instruction) at xFF go to page x+1 |
| C4 | Stack: 3 nested JMS/BBL return correctly; a 4th JMS overwrites the oldest |
| C5 | JCN: all 16 condition codes × (`acc`==0 or not) × `cy` × `test` |
| C6 | DCL: all 8 bank codes give the §6.5 lines on SRC and on I/O instructions |
| C7 | Reset: after reset, fetch starts at 0x000 with `acc` = `cy` = 0 |
| C8 | No X or Z on any output for fully driven inputs (4-state run, as for the 74181) |
| C9 | Random programs: the RTL and Rook's reference model agree on every pin, every clock, for N random programs (N set by Rook, at least 10,000 programs × 1,000 cycles) |

## 9. Acceptance tests (software not written by this team)
1. **Busicom 141-PF calculator firmware**, the program the 4004 was built for, running on `mcs4_system` with a model of the printer/keyboard I/O: key in sums and check the printed results. Source: the reconstructed and commented listing published by the 4004 restoration project (Tim McNerney et al.). **License must be confirmed before use. If it doesn't allow it, drop to 2 and 3 and say so in the release.**
2. **Example programs from the MCS-4 Users Manual** (e.g. multi-digit decimal addition, subtraction), typed in from the manual. Expected results come from the manual's text.
3. **Instruction-level comparison against an independent, existing 4004 emulator** (to be chosen by Rook; it must not be written by this team), run on the same random programs as C9.

## 10. Datasheet check
Source read: Intel *MCS-4 Micro Computer Set Users Manual* (Feb 1973 scan, OCR text layer), on 2026-11-14 by Vera. Page numbers are the manual's printed page numbers. The OCR is noisy, so items marked "page image" still need someone to read the scan directly.

- [x] Negative logic in the original (p.6), so our positive-logic choice is a deliberate deviation (§1)
- [x] 8 clock periods per instruction cycle, 10.8 µs (p.6, p.28)
- [ ] §2 pin numbers: SYNC = 8 and TEST = 10 confirmed; the rest are in a figure (page image)
- [x] §4 bus contents: A1–A3 address, M1/M2 OPR/OPA, X2/X3 SRC address (p.6, p.15, p.30)
- [x] §4 CM lines: CM-ROM + CM-RAMi at A3 (meaningless to RAMs), at M2 for I/O-group, at X2 for SRC (p.15). Fig. 4's exact edges: page image
- [x] §5 reset: static FFs cleared, index registers need ≥ 64 clock periods (p.10)
- [x] §3 stack: a 4th JMS loses the deepest address (p.13)
- [x] §6.2 page quirk for JCN (words 254/255), ISZ (254/255), FIN (at xFF), JIN (at xFF) (p.30–32)
- [x] JCN condition equation and bit order (p.32)
- [x] DAC, DAA, TCS, TCC, KBP, RAL, RAR, IAC (p.35–36)
- [x] SUB/SBM `cy` sense. The manual page is unreadable in OCR; confirmed instead from the pyntel4004 docs, which quote the Assembly Language Programming Manual: "complementing each bit of R and adding … plus the complement of the carry bit"; a borrow is indicated by `cy` = 1 at the start. **Secondary source. Upgrade to primary when someone reads the page image.**
- [ ] §6.5 DCL row-by-row mapping (page image, p.36)
- [x] §7 4002: X2 nibble = 2 bits chip + 2 bits register, X3 = character (p.15); ROM uses the X2 nibble only and ignores X3 (p.15)
- [ ] §7 4002-1/-2 strap mapping (page image)
- [ ] Busicom 141-PF listing license (§9)
