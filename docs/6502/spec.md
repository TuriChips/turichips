# Spec: MOS 6502 (Chip #3), DRAFT

Status: **DRAFT v0, not normative.** Written by Igris on 2026-11-16, after the 8080's release, to start roadmap chip #3. Nobody builds from this until every **[check]** item is confirmed against the MOS manuals (§10) and Sai signs it off. It then moves to `TuriChips/chip-6502`, the same way the 4004 and 8080 specs did.

Facts marked **[check]** are from memory and must be read from the page (as page images where the scan's text is unreliable) before this is normative. Choices that are ours, not MOS's, are marked *Decision*.

Sources for §10 (bitsavers, fetched to a scratch dir, never committed):
- MOS Technology, *MCS6500 Microcomputer Family Hardware Manual*, 6500-10A, January 1976 (pins, timing, interrupts, reset).
- MOS Technology, *MCS6500 Microcomputer Family Programming Manual*, 6500-50A, January 1976 (instructions, addressing modes, flags, decimal mode).

## 1. Scope
- The **NMOS 6502 CPU**, cycle-accurate at its pins: every clock cycle's address, data direction, R/W and SYNC is specified (§4), including the "dummy" bus cycles the real part makes. Those are visible at the pins, and real software and hardware depend on some of them.
- **Not in scope:** the 65C02 and other CMOS variants, the 6507/6510 package variants (the Atari 2600's 6507 is chip #5's business), electrical timing, the two-phase clock's waveforms.
- Logic convention: positive logic. Active-low pins keep a `_n` suffix (`irq_n`, `nmi_n`, `res_n`), as the 8080 did with `wr_n`.
- Clock: *Decision.* One rising-edge model clock `clk` per φ2 cycle. Every 6502 cycle is one bus access, read or write [check: no idle bus cycles on the NMOS part].

## 2. Pins (top module `m6502`)
| Signal | Dir | Width | Meaning [check all against the Hardware Manual] |
|--------|-----|-------|---------|
| `clk` | in | 1 | Model clock, one per cycle |
| `res_n` | in | 1 | RESET, active low |
| `a` | out | 16 | A15–A0, driven in every cycle |
| `d_in` | in | 8 | D7–D0 from memory or I/O |
| `d_out` | out | 8 | D7–D0 driven by the CPU in write cycles |
| `d_oe` | out | 1 | 1 in write cycles (split bus, no tri-states, as for the 4004 and 8080) |
| `rw` | out | 1 | R/W: 1 = read, 0 = write |
| `sync` | out | 1 | SYNC: 1 in an opcode-fetch cycle |
| `rdy` | in | 1 | RDY: 0 halts the CPU on a **read** cycle [check: NMOS ignores RDY on write cycles] |
| `irq_n` | in | 1 | Maskable interrupt, level-sensitive, gated by the I flag |
| `nmi_n` | in | 1 | Non-maskable interrupt, edge-sensitive (falling edge) |
| `so_n` | in | 1 | Set Overflow: a falling edge sets V [check timing] |

## 3. Programmer's model
| Name | Width | Reset value | Notes |
|------|-------|-------------|-------|
| `A`, `X`, `Y` | 8 each | not reset [check] | *Decision* proposed: unreset, with a C8 preamble as for the 8080 |
| `S` | 8 | [check: the reset sequence decrements S by 3 without writing] | Stack in page 1, address `{01, S}` |
| `PC` | 16 | from the reset vector FFFC/FFFD | |
| `P` | 8 | I = 1 after reset [check]; others not reset [check] | `N V 1 B D I Z C`, bit 5 reads 1 when pushed. **B exists only in the pushed byte**: 1 from PHP/BRK, 0 from IRQ/NMI [check] |

Vectors: NMI FFFA/FFFB, RESET FFFC/FFFD, IRQ and BRK FFFE/FFFF.

## 4. Cycle timing (normative once checked)
To be written as a total table, like the 8080's: for each addressing mode × instruction class (read, write, read-modify-write, branch, stack, jump, interrupt sequence), every cycle's `a`, `rw`, `sync`, and `d_out` when writing. This is where most 6502 bugs live, so every cycle must be pinned, including the dummy ones [check each against the Hardware Manual's cycle tables]:
- Indexed reads crossing a page take an extra cycle, with a dummy read at the un-carried address. Indexed writes and RMW **always** take that cycle.
- Read-modify-write instructions write the **unmodified** value back once, then the modified value (two write cycles).
- Branches: 2 cycles not taken, 3 taken, 4 taken across a page, with dummy reads.
- Implied and accumulator instructions do a dummy read of the next byte.
- Interrupt sequence (IRQ, NMI, BRK, RESET): 7 cycles. RESET does its three stack accesses as reads, not writes.

## 5. Reset
`res_n` low for at least [check] cycles. Then the 7-cycle sequence, the vector fetch from FFFC/FFFD, and the first opcode fetch. *Decision* to write down: pins while `res_n` = 0, and when comparison starts (the first SYNC after reset), as for the 4004 and 8080.

## 6. Instructions (normative once checked)
151 documented opcodes, 56 instructions, 13 addressing modes [check]. Each will get an exact table row (encoding, addressing mode, cycles, flags), as the 8080's §6.1.

Quirks that must each be pinned to a source line before C1 is written:
- **`JMP ($xxFF)`** fetches the high byte from `$xx00`, not `$(xx+1)00` (no carry into the page) [check].
- **Decimal mode (D = 1) on the NMOS part:** ADC/SBC give correct BCD results and C for valid BCD inputs. N, V and Z are the documented trouble spot: on NMOS they follow intermediate binary results, not the BCD answer [check]. *Decision* needed: specify the NMOS behaviour exactly (from a primary source), or test only valid BCD inputs and C/A.
- **The B flag:** not a real flip-flop; only the pushed copy differs (BRK/PHP vs IRQ/NMI) [check].
- **Interrupt timing:** IRQ/NMI are sampled during the last cycle of an instruction [check: which phase], a taken branch without page cross delays the IRQ by one instruction, and an NMI arriving during a BRK's vector fetch "hijacks" it [check].
- **RDY on NMOS** only stops read cycles [check].
- **Undocumented opcodes** (105 of the 256 bytes): *Decision* proposed, as for the 4004 and 8080: not tested and excluded from C8, unless a primary source defines them. The Programming Manual doesn't.

## 7. System for tests
`m6502_system`: one `m6502`, 64 KiB RAM from `$readmemh`, the reset/IRQ/NMI vectors in that image, a console output port for test programs, and the `bus_conflict` idea from the 8080's system.

## 8. Behaviours to test (draft)
| ID | Behaviour |
|----|-----------|
| C1 | Every documented opcode in every addressing mode: registers, memory and flags per §6 |
| C2 | Pin timing per §4 for every addressing mode, including dummy cycles, page crossings and RMW double writes |
| C3 | RDY: stops reads at any read cycle, ignored on writes |
| C4 | Interrupts: IRQ masked by I, NMI edge, BRK, B in the pushed P, the branch delay, NMI hijacking BRK |
| C5 | Decimal mode, per the §6 decision |
| C6 | Reset sequence and vectors |
| C7 | No X/Z, no bus conflict, with the positive-case test (8080 lesson) |
| C8 | Random programs vs Beru's reference model, ≥ 10,000 × 1,000 instructions, pins every cycle |

## 9. Acceptance test candidates (licences to be checked before use, as for the 8080)
1. **Klaus Dormann's 6502 functional test** (and its decimal test): widely used to validate 6502 cores. Licence [check, believed GPL-3.0]. Same rule as the 8080 exercisers: fetched at test time, never committed.
2. **Per-instruction, per-cycle test vectors published for NMOS 6502 emulators** (e.g. Tom Harte's SingleStepTests): they record every bus cycle, which suits C2/C8. Licence and provenance [check].
3. **Example programs from the MOS Programming Manual**, typed in from the page images, expected values from the manual's text where printed.
4. **An independent existing 6502 emulator** for instruction-level comparison (Beru chooses, MAME's core first, licence recorded).

## 10. Datasheet check
Not started. Every [check] gets a line here with the page it was confirmed on.
