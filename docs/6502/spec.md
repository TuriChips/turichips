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
| `rdy` | in | 1 | RDY: 0 delays the current cycle, **only if it's a read** (Hardware Manual §1.4.1.2.8, p.37: "will not stop the processor in a cycle in which a WRITE operation is being performed … will execute that cycle and will then stop in the next READ cycle (R/W = 1)"). The CPU repeats the stopped read cycle with the same address while `rdy` = 0 |
| `irq_n` | in | 1 | Maskable interrupt, level-sensitive, gated by the I flag |
| `nmi_n` | in | 1 | Non-maskable interrupt, edge-sensitive (falling edge) |
| `so_n` | in | 1 | Set Overflow: a falling edge sets V [check timing] |

## 3. Programmer's model
| Name | Width | Reset value | Notes |
|------|-------|-------------|-------|
| `A`, `X`, `Y` | 8 each | **not reset** (p.126: "internal registers may be initialized to any random condition") | *Decision*: unreset, with a C8 preamble as for the 8080 |
| `S` | 8 | **not initialised** (p.127: the only automatic reset actions are setting I and loading PC; programs start with `LDX #n; TXS`). The reset sequence reads at {01,S}, {01,S−1}, {01,S−2} (Example 9.1); whether S is left decremented by 3 is not stated, so *Decision*: S after reset is **not compared**, and the C8 preamble sets it | Stack in page 1, address `{01, S}` |
| `PC` | 16 | from the reset vector FFFC/FFFD | |
| `P` | 8 | **I = 1** after reset (p.127: "turn on the interrupt disable bit"); the others not reset (the same page lists no other automatic action) | `N V 1 B D I Z C`, bit 5 reads 1 when pushed. **B exists only in the pushed byte**: 1 from PHP/BRK, 0 from IRQ/NMI [check] |

Vectors: NMI FFFA/FFFB, RESET FFFC/FFFD, IRQ and BRK FFFE/FFFF.

## 4. Cycle timing (normative once checked)
**Source:** Hardware Manual **Appendix A, "Summary of Single Cycle Execution"** (PDF pages 168 to the end, A-1 onward), which "contains an outline of the data on both the address bus and the data bus for each cycle of the various processor instructions". It restates on A-1 that the processor "will not stop in any cycle where R/W is a 0". It is being transcribed into this section page by page. To be written as a total table, like the 8080's: for each addressing mode × instruction class (read, write, read-modify-write, branch, stack, jump, interrupt sequence), every cycle's `a`, `rw`, `sync`, and `d_out` when writing. This is where most 6502 bugs live, so every cycle must be pinned, including the dummy ones [check each against the Hardware Manual's cycle tables]:
- Indexed reads crossing a page take an extra cycle, with a dummy read at the un-carried address. Indexed writes and RMW **always** take that cycle.
- Read-modify-write instructions write the **unmodified** value back once, then the modified value (two write cycles).
- Branches: 2 cycles not taken, 3 taken, 4 taken across a page, with dummy reads.
- Implied and accumulator instructions do a dummy read of the next byte.
- Interrupt sequence (IRQ, NMI, BRK): **7 cycles**, from Example 9.2 (p.131), shown there with S = FF:
  1. opcode fetch at PC ("Finish Previous Operation");
  2. fetch at PC again, with the opcode discarded ("Force a BRK Instruction, Hold P-Counter");
  3. push PCH at 01FF;
  4. push PCL at 01FE;
  5. push P at 01FD;
  6. read vector low at FFFE (FFFA for NMI);
  7. read vector high at FFFF (FFFB) and set I;

  then the opcode fetch at the vector. For BRK itself, cycle 2's address is PC + 1 and the pushed PC is PC + 2 (p.144) [check: BRK's own cycle table]. **RESET**, after `res_n` rises (Example 9.1, p.127): 7 cycles. 1 and 2 at undefined addresses ("?", "? + 1"), 3–5 at {01,S}, {01,S−1}, {01,S−2} as **reads** ("the read/write line is disabled so that no writes to stack are accomplished"), 6 FFFC, 7 FFFD, then 8 the first opcode at the vector.

### 4.1 Per-cycle tables (transcribed from Hardware Manual Appendix A, page images)
Notation as in Appendix A: `{H, L}` is the address with high byte H and low byte L, and `00, X` is zero page. Every row's data bus is a read (`rw` = 1) unless marked **W**. "(disc.)" means the CPU reads and discards the value: the cycle happens at the pins and is compared. T0 is always the opcode fetch with `sync` = 1, and the next T0 is the next instruction's fetch.

**A.1 Single-byte instructions, 2 cycles** (A-2): ASL A, CLC, CLD, CLI, CLV, DEX, DEY, INX, INY, LSR A, NOP, ROL A, SEC, SED, SEI, TAX, TAY, TSX, TXA, TXS, TYA. (ROR A isn't listed: [check] against the instruction list.)
| Tn | `a` | data | note |
|----|-----|------|------|
| T0 | PC | opcode | fetch |
| T1 | PC+1 | opcode (disc.) | the next instruction's opcode is read and ignored |
| T0 | PC+1 | opcode | next instruction |

**A.2 Internal execution on memory data** (A-2): ADC, AND, BIT, CMP, CPX, CPY, EOR, LDA, LDX, LDY, ORA, SBC. The result is formed while the next opcode is fetched.

A.2.1 Immediate (2 cycles), A-3:
| T0 PC opcode | T1 PC+1 data | T0 PC+2 next opcode |
|---|---|---|

A.2.2 Zero page (3):
| T0 PC opcode | T1 PC+1 ADL | T2 {00, ADL} data | T0 PC+2 |
|---|---|---|---|

A.2.3 Absolute (4):
| T0 PC opcode | T1 PC+1 ADL | T2 PC+2 ADH | T3 {ADH, ADL} data | T0 PC+3 |
|---|---|---|---|---|

A.2.4 (Indirect, X) (6):
| T0 PC opcode | T1 PC+1 BAL | T2 {00, BAL} (disc.) | T3 {00, BAL+X} ADL | T4 {00, BAL+X+1} ADH | T5 {ADH, ADL} data | T0 PC+2 |
|---|---|---|---|---|---|---|

The zero-page pointer arithmetic stays in page 00 (the manual writes the high byte as 00) [check: wrap of BAL+X+1 at FF, from the 8-bit page-zero rule].

## 5. Reset
While `res_n` = 0 the CPU is "guaranteed to be in a Read state" (`rw` = 1), and after release it stays in Read until it has fetched the vector (p.126). Then the 7-cycle sequence in §4, and the first opcode fetch in cycle 8. Minimum low time for `res_n`: [check, Hardware Manual].
*Decisions*: while `res_n` = 0, `rw` = 1, `d_oe` = 0, and `a`/`sync` are not compared. In reset cycles 1 and 2, `a` is not compared (the manual prints "?"). Comparison of everything starts at the first SYNC (cycle 8), **preamble included, with no exemption window**: the C8 preamble writes A, X, Y, S and P before anything reads them, as for the 8080 (Beru, turichips#26).

## 6. Instructions (normative once checked)
151 documented opcodes, 56 instructions, 13 addressing modes [check]. Each will get an exact table row (encoding, addressing mode, cycles, flags), as the 8080's §6.1.

Quirks that must each be pinned to a source line before C1 is written:
- **`JMP ($xxFF)`** fetches the high byte from `$xx00`, not `$(xx+1)00` (confirmed §10: Programming Manual Example 9.6, p.141, fetches ADH from address "IAH, IAL+1" after "Add 1 to IAL", an 8-bit add to the low byte with no carry into IAH). Bus cycles: 1 opcode at PC, 2 IAL at PC+1, 3 IAH at PC+2, 4 ADL at {IAH, IAL}, 5 ADH at {IAH, IAL+1 mod 256}, then the next opcode fetch at {ADH, ADL}.
- **Which instructions change I and D** (confirmed §10, Programming Manual §3.2–3.3, pp.26–27): I only by BRK, CLI, PLP, RTI, SEI (and the interrupt/reset sequences, p.127/131); **D only by CLD, PLP, RTI, SED**. So on the NMOS part **an interrupt or BRK does not clear D**, and D is random after reset (p.127 lists I as the only flag reset sets). A test or the C8 preamble must clear or set D explicitly.
- **Decimal mode (D = 1)**, what the manual says (confirmed §10, Programming Manual §2.2.1.2–2.2.2, pp.13–14): with D = 1, ADC and SBC produce packed-BCD results (Example 2.12: 79 + 14 = 93), and **C** tells the user whether the result "exceeds … 99 decimal" (ADC). For SBC, C = 1 means no borrow (A − M − C̄). **The manual says nothing about N, V or Z after a decimal operation.**
  - **Open decision, for Beru and Sai** (C8 compares every cycle, so any random program doing SED; ADC; PHP or a branch exposes N/V/Z, and "unspecified" isn't an option unless C8 avoids decimal mode). Options:
    - **(a)** Specify the real NMOS behaviour, citing a named secondary source, since the MOS manual is silent. This is testable with Dormann's decimal test in its NMOS-flags mode (§9).
    - **(b)** Specify only A and C in decimal mode, make C5 test only those, and keep C8's generator in binary mode (D = 0 always). N/V/Z after decimal ADC/SBC become "not specified, never tested". That's simpler, but a real-software difference could go unseen.
    - **(c)** Pick a clean rule of our own (e.g. N and Z from the BCD result, V as in binary) and test it. That's easy to specify, but deliberately unlike the real chip.
  - My recommendation is **(a)**, because the lab rebuilds the real chip. But it rests on a secondary source, so it's Sai's call.
- **The B flag and BRK** (confirmed §10, Programming Manual §9.11, p.144): BRK pushes the address of the **second byte after BRK** (PC + 2) and P, then loads PC from FFFE/FFFF. In the pushed P, **B (bit 4, the manual's `AND #$10`) is 1 for BRK and 0 for an IRQ**. **BRK sets I** (confirmed §10): an interrupt is serviced by **forcing a BRK** (Example 9.2, p.131, cycle 2: "Force a BRK Instruction"), and that shared sequence does "Vector Low → PCL and Set I" in cycle 7. The text adds that "the interrupt disable is turned on at this point by the microprocessor automatically". So p.144's "changes no values in either the registers or the flags" is read as "no register or arithmetic flag other than I". This is *Decision* wording, built on the p.131 table. Still [check]: B for PHP and NMI.
- **Interrupt timing:** IRQ/NMI are sampled during the last cycle of an instruction [check: which phase], a taken branch without page cross delays the IRQ by one instruction, and an NMI arriving during a BRK's vector fetch "hijacks" it [check].
- **RDY** only stops read cycles (confirmed, p.37). Stimulus rule (*Decision*, as for the 8080): tests change `rdy` only on the clock edge that starts a cycle. The manual says RDY "should change during the Phase One clock pulse" and is "recognized during the next Phase Two", which maps to that edge in our one-clock model.
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
Every [check] gets a line here with the page it was confirmed on. Both 1976 scans (bitsavers) have **no text layer**, so every check is read from page images (poppler, toolchain#35). Page offset: Programming Manual printed page *n* = PDF page *n* + 13 up to about p.92, and *n* + 16 by p.138 (unnumbered inserts), so check the printed number on each rendered page.
- [ ] §4 per-cycle table from Appendix A (PDF 168–182): A-1, A-2, A-3 transcribed into §4.1 (single-byte; immediate, zero page, absolute, (ind,X) reads). Next: A-4 onward.
- [x] RDY (Hardware Manual §1.4.1.2.8, p.37, page image; offset printed n = PDF n + 13): stops only read cycles; a write in progress completes, and the stop happens at the next read; change in φ1, recognised in the next φ2. Also p.32: "The address bus will always contain known data as detailed in Appendix A", the per-cycle table to read for §4.
- [x] I and D (§3.2–3.3, pp.26–27, page images): I changed only by BRK, CLI, PLP, RTI, SEI; D only by CLD, PLP, RTI, SED (so interrupts don't clear D); SED makes ADC/SBC decimal. Decimal ADC/SBC (§2.2.1.2–2.2.2, pp.13–14, page images): BCD result and C defined; **N/V/Z in decimal mode not stated anywhere in the manual**, so it's an open decision (§6).
- [x] Reset (§9.1–9.3, pp.125–127, page images): Read state while reset is low and until the vector is fetched; Example 9.1's 7-cycle start sequence (stack accesses are reads); the only automatic actions are I = 1 and PC ← vector; registers random. Open: minimum reset low time (Hardware Manual), S after the sequence (*Decision*: not compared).
- [x] Interrupt sequence (§9.5, Example 9.2, p.131, page image): 7 cycles as listed in §4. Cycle 2 forces a BRK, cycle 7 sets I, and the text says "the interrupt disable is turned on … automatically". So BRK sets I.
- [x] BRK (§9.11, p.144, page image): pushes PC + 2 and P, vector FFFE/FFFF, pushed B = 1 for BRK, 0 for IRQ, B is bit 4 (`AND #$10`). Open: B on PHP/NMI (I after BRK is resolved by p.131 above).
- [x] `JMP ($xxFF)` page wrap: §6.6 (p.92) is silent, but **§9.8.1, Example 9.6 "Illustration of JMP Indirect" (p.141, page image)** gives the cycle table: cycle 4 reads ADL at "IAH, IAL" while doing "Add 1 to IAL", and cycle 5 reads ADH at "IAH, IAL+1". The increment is to IAL alone, so the high-byte pointer stays in the same page. This is a primary-source basis for the wrap, read from the bus addresses, not stated as a caution.
