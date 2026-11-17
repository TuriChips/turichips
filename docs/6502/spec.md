# Spec: MOS 6502 (Chip #3), DRAFT

Status: **DRAFT v0, not normative.** Written by Igris on 2026-11-16, after the 8080's release, to start roadmap chip #3. Nobody builds from this until every **[check]** item is confirmed against the MOS manuals (§10) and Sai signs it off. It then moves to `TuriChips/chip-6502`, the same way the 4004 and 8080 specs did.

Facts marked **[check]** are from memory and must be read from the page (as page images where the scan's text is unreliable) before this is normative. Choices that are ours, not MOS's, are marked *Decision*.

Sources for §10 (bitsavers, fetched to a scratch dir, never committed):
- MOS Technology, *MCS6500 Microcomputer Family Hardware Manual*, 6500-10A, January 1976 (pins, timing, interrupts, reset).
- MOS Technology, *MCS6500 Microcomputer Family Programming Manual*, 6500-50A, January 1976 (instructions, addressing modes, flags, decimal mode).

## 1. Scope
- The **NMOS 6502 CPU**, cycle-accurate at its pins: every clock cycle's address, data direction, R/W and SYNC is specified (§4), including the "dummy" bus cycles the real part makes. Those are visible at the pins, and real software and hardware depend on some of them.
- **Revision** (*Decision*): the **post-June-1976 NMOS 6502, with ROR**. The Hardware Manual (A-7) notes "The ROR instruction will be available on MCS650X microprocessors after June, 1976". So earlier parts lack ROR, which is why A.1's 1976 list has no ROR A. We specify the version with ROR (ROR A, and ROR in every memory mode) because that's the 6502 later used in the Atari 2600 and NES (roadmap chips #5 and #11).
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

  then the opcode fetch at the vector. For BRK itself, cycle 2's address is **PC + 1**, and for a hardware interrupt it's **PC** (Appendix A.5.4, A-11). The pushed PC is PC + 2 for BRK (p.144). **RESET**, after `res_n` rises (Example 9.1, p.127): 7 cycles. 1 and 2 at undefined addresses ("?", "? + 1"), 3–5 at {01,S}, {01,S−1}, {01,S−2} as **reads** ("the read/write line is disabled so that no writes to stack are accomplished"), 6 FFFC, 7 FFFD, then 8 the first opcode at the vector.

### 4.0 What is compared, every cycle
One model clock = one 6502 cycle, and **every cycle is a bus cycle**: Appendix A lists an address, data and R/W for every Tn of every instruction (A-1: "The address bus will always contain known data", Hardware Manual p.32). So:

| Pin | Compared | Rule |
|-----|----------|------|
| `a` | every cycle | the address in the §4.1 row for that cycle, including dummy (disc.) cycles |
| `rw` | every cycle | 1 on read rows, 0 on **W** rows |
| `sync` | every cycle | 1 exactly on T0 (opcode fetch) rows, else 0 |
| `d_oe` | every cycle | = NOT `rw`: 1 exactly on **W** rows |
| `d_out` | only when `d_oe` = 1 | the value the row writes (register, PCH/PCL/P on pushes, unmodified then modified data on RMW) |
| `d_in` | (input) | the CPU must use it only on the rows that fetch a value; on (disc.) rows its value must not affect any register or flag |

- **RDY** (`rdy` = 0) holds a **read** cycle. The same row repeats, with the same `a`, `rw` = 1 and `sync`, until `rdy` = 1 at the cycle edge. A write cycle in progress completes, and the hold takes effect at the next read (§2, Hardware Manual p.37).
- While `res_n` = 0, and in reset cycles 1–2, see §5.
- **Comparison starts** at the first `sync` after reset (§5) and never pauses after that. There's no exemption window (8080 lesson).

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

A.2.5 Absolute,X / Absolute,Y (4, or 5 on a page cross), A-4:
| T0 PC opcode | T1 PC+1 BAL | T2 PC+2 BAH | T3 {BAH + C, BAL + index} data* | T4* {BAH + 1, BAL + index} data | T0 PC+3 |
|---|---|---|---|---|---|

\* "If the page boundary is crossed in the indexing operation, the data fetched in T3 is ignored. If page boundary is not crossed, the T4 cycle is bypassed." The manual writes T3's high byte as "BAH + C … Carry is 0 or 1 as required from previous add". **Reading** (*Decision* pending [check] against an independent per-cycle source, §9 item 2): on a page cross, T3's address is the **uncarried** {BAH, (BAL + index) mod 256}, and T4 is {BAH + 1, (BAL + index) mod 256}. That's the only reading in which T4 is needed.

A.2.6 Zero page,X / Zero page,Y (4), A-4:
| T0 PC opcode | T1 PC+1 BAL | T2 {00, BAL} (disc.) | T3 {00, BAL + index} data | T0 PC+2 |
|---|---|---|---|---|

"No page crossing": the index add stays in page 00 (wraps mod 256).

A.2.7 (Indirect),Y (5, or 6 on a page cross), A-5:
| T0 PC opcode | T1 PC+1 IAL | T2 {00, IAL} BAL | T3 {00, IAL + 1} BAH | T4 {BAH + C, BAL + Y} data* | T5* {BAH + 1, BAL + Y} data | T0 PC+2 |
|---|---|---|---|---|---|---|

\* Same footnote and the same reading of "BAH + C" as A.2.5. IAL + 1 stays in page 00 [check: IAL = FF].

**A.3 Stores** (A-5): STA, STX, STY. "The fetch of data is replaced by a WRITE (R/W = 0) cycle. No overlapping occurs and **no shortening of the instruction time occurs on indexing operations**": indexed stores always take the page-cross cycle count.

A.3.1 Zero page (3):
| T0 PC opcode | T1 PC+1 ADL | T2 {00, ADL} **W** register | T0 PC+2 |
|---|---|---|---|

A.3.2 Absolute (4), A-6:
| T0 PC opcode | T1 PC+1 ADL | T2 PC+2 ADH | T3 {ADH, ADL} **W** | T0 PC+3 |
|---|---|---|---|---|

A.3.3 (Indirect, X) (6):
| T0 PC | T1 PC+1 BAL | T2 {00, BAL} (disc.) | T3 {00, BAL+X} ADL | T4 {00, BAL+X+1} ADH | T5 {ADH, ADL} **W** | T0 PC+2 |
|---|---|---|---|---|---|---|

A.3.4 Absolute,X / Absolute,Y (**always 5**):
| T0 PC | T1 PC+1 BAL | T2 PC+2 BAH | T3 {BAH (+C), BAL + index} (disc.) | T4 {ADH, ADL} **W** | T0 PC+3 |
|---|---|---|---|---|---|

A.3.5 Zero page,X / Y (4), A-7:
| T0 PC | T1 PC+1 BAL | T2 {00, BAL} (disc.) | T3 {00, BAL + index} **W** | T0 PC+2 |
|---|---|---|---|---|

A.3.6 (Indirect),Y (**always 6**):
| T0 PC | T1 PC+1 IAL | T2 {00, IAL} BAL | T3 {00, IAL+1} BAH | T4 {**BAH**, BAL + Y} (disc.) | T5 {ADH, ADL} **W** | T0 PC+2 |
|---|---|---|---|---|---|---|

**This settles the "BAH + C" reading**: A.3.6 writes the discarded read's high byte as plain **BAH**, the uncarried page, while A.3.4 uses the "BAH + C" wording for the same kind of cycle. So the dummy read before an indexed access is at the **uncarried** address, and the reading in A.2.5/A.2.7 is now backed by the manual itself. Still to confirm independently in C8 (§9 item 2).

**A.4 Read-modify-write** (A-7): ASL, DEC, INC, LSR, ROL, ROR. They load the operand, modify it and store the result back at the same address. **Every mode writes twice: first the unmodified value, then the modified value** (A-8/A-9, R/W = 0 in both cycles). This is visible at the pins and compared.

A.4.1 Zero page (5), A-8:
| T0 PC | T1 PC+1 ADL | T2 {00, ADL} data | T3 {00, ADL} **W** data (unmodified) | T4 {00, ADL} **W** modified | T0 PC+2 |
|---|---|---|---|---|---|

A.4.2 Absolute (6):
| T0 PC | T1 PC+1 ADL | T2 PC+2 ADH | T3 {ADH, ADL} data | T4 {ADH, ADL} **W** data | T5 {ADH, ADL} **W** modified | T0 PC+3 |
|---|---|---|---|---|---|---|

A.4.3 Zero page,X (6): the manual writes "BAL + X **(without carry)**" for T3–T5, so the address stays in page 00.
| T0 PC | T1 PC+1 BAL | T2 {00, BAL} (disc.) | T3 {00, BAL+X} data | T4 {00, BAL+X} **W** data | T5 {00, BAL+X} **W** modified | T0 PC+2 |
|---|---|---|---|---|---|---|

A.4.4 Absolute,X (**always 7**), A-9:
| T0 PC | T1 PC+1 BAL | T2 PC+2 BAH | T3 {BAH (+C), BAL+X} (disc.) | T4 {ADH, ADL} data | T5 {ADH, ADL} **W** data | T6 {ADH, ADL} **W** modified | T0 PC+3 |
|---|---|---|---|---|---|---|---|
T3 is the same dummy-read cycle as A.3.4, at the uncarried address per A.3.6.

**A.5 Miscellaneous** (A-9): branches, BRK, JMP, JSR, PHA, PHP, PLA, PLP, RTI, RTS.

A.5.1 PHP, PHA (3): "Stack Ptr." = {01, S}; S decrements after the write [check: the S update isn't printed on A-9].
| T0 PC | T1 PC+1 opcode (disc.) | T2 {01, S} **W** register | T0 PC+1 |
|---|---|---|---|

A.5.2 PLP, PLA (4), A-10:
| T0 PC | T1 PC+1 (disc.) | T2 {01, S} (disc.) | T3 {01, S+1} data | T0 PC+1 |
|---|---|---|---|---|

A.5.3 JSR (6). The **high byte is fetched after the pushes**:
| T0 PC | T1 PC+1 ADL | T2 {01, S} (disc.) | T3 {01, S} **W** PCH | T4 {01, S−1} **W** PCL | T5 PC+2 ADH | T0 {ADH, ADL} |
|---|---|---|---|---|---|---|
The pushed PC is the address of JSR's **last byte (PC+2)**, confirmed by RTS's table (A.5.7: the next fetch is at the pulled PC **+ 1**).

A.5.4 BRK, and IRQ/NMI/RESET (7), A-11:
| T0 PC opcode (or forced BRK) | T1 **PC+1** (disc.); **PC on a hardware interrupt** | T2 {01, S} **W** PCH | T3 {01, S−1} **W** PCL | T4 {01, S−2} **W** P | T5 FFFE (NMI FFFA, RES FFFC) ADL | T6 FFFF (FFFB, FFFD) ADH | T0 {ADH, ADL} |
|---|---|---|---|---|---|---|---|
For RESET, T2–T4 are reads, not writes (Programming Manual Example 9.1, §4 above).

A.5.5 RTI (6):
| T0 PC | T1 PC+1 (disc.) | T2 {01, S} (disc.) | T3 {01, S+1} P | T4 {01, S+2} PCL | T5 {01, S+3} PCH | T0 {PCH, PCL} |
|---|---|---|---|---|---|---|

A.5.6.1 JMP absolute (3), A-12:
| T0 PC | T1 PC+1 ADL | T2 PC+2 ADH | T0 {ADH, ADL} |
|---|---|---|---|

A.5.6.2 JMP (indirect) (5): matches Programming Manual Example 9.6 (§6).
| T0 PC | T1 PC+1 IAL | T2 PC+2 IAH | T3 {IAH, IAL} ADL | T4 {IAH, IAL+1} ADH | T0 {ADH, ADL} |
|---|---|---|---|---|---|

A.5.7 RTS (6):
| T0 PC | T1 PC+1 (disc.) | T2 {01, S} (disc.) | T3 {01, S+1} PCL | T4 {01, S+2} PCH | T5 {PCH, PCL} (disc.) | T0 {PCH, PCL} **+ 1** |
|---|---|---|---|---|---|---|

A.5.8 Branches BCC BCS BEQ BMI BNE BPL BVC BVS (2, 3 or 4), A-13:
| Tn | `a` | data | when |
|----|-----|------|------|
| T0 | PC | opcode | always |
| T1 | PC+1 | offset | always |
| T2 | {PCH, (PCL + 2 + offset) mod 256}, "PC + 2 + offset (w/o carry)" | opcode (disc.) | only if taken |
| T3 | PC + 2 + offset, **with** carry | opcode (disc.) | only if taken **and** the page is crossed |
| T0 | the target (taken) or PC+2 (not taken) | opcode | next instruction |

So a taken branch's first extra cycle reads at the **uncarried** target, the same pattern as the indexed reads above. [check: T2's high byte is PC+2's page, since "w/o carry" names only the low-byte add.]

**Appendix A is fully transcribed.** §4.0 now states the per-cycle comparison rule. Interrupt timing is in §6.

## 5. Reset
While `res_n` = 0 the CPU is "guaranteed to be in a Read state" (`rw` = 1), and after release it stays in Read until it has fetched the vector (p.126). Then the 7-cycle sequence in §4, and the first opcode fetch in cycle 8. Minimum low time for `res_n`: [check, Hardware Manual].
*Decisions*: while `res_n` = 0, `rw` = 1, `d_oe` = 0, and `a`/`sync` are not compared. In reset cycles 1 and 2, `a` is not compared (the manual prints "?"). Comparison of everything starts at the first SYNC (cycle 8), **preamble included, with no exemption window**: the C8 preamble writes A, X, Y, S and P before anything reads them, as for the 8080 (Beru, turichips#26).

## 6. Instructions (normative once checked)
**151 documented opcodes, 56 instructions, 13 addressing modes** (confirmed §10, Programming Manual **Appendix D, "Operation Code Instruction Listing Hexadecimal Sequence"**, D-2 to D-5, page images. Every byte 00–FF is listed, and the other **105 are marked "Future Expansion"**, so they're undocumented by MOS).

### 6.0 Opcode map (Appendix D, D-2 to D-5)
`·` = "Future Expansion" (undocumented; not tested, §6 decision). `(zp,X)`/`(zp),Y` are the manual's "(Indirect,X)"/"(Indirect),Y", and `(abs)` is "JMP Indirect".

| hi\lo | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | A | B | C | D | E | F |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | BRK | ORA (zp,X) | · | · | · | ORA zp | ASL zp | · | PHP | ORA # | ASL A | · | · | ORA abs | ASL abs | · |
| 1 | BPL rel | ORA (zp),Y | · | · | · | ORA zp,X | ASL zp,X | · | CLC | ORA abs,Y | · | · | · | ORA abs,X | ASL abs,X | · |
| 2 | JSR abs | AND (zp,X) | · | · | BIT zp | AND zp | ROL zp | · | PLP | AND # | ROL A | · | BIT abs | AND abs | ROL abs | · |
| 3 | BMI rel | AND (zp),Y | · | · | · | AND zp,X | ROL zp,X | · | SEC | AND abs,Y | · | · | · | AND abs,X | ROL abs,X | · |
| 4 | RTI | EOR (zp,X) | · | · | · | EOR zp | LSR zp | · | PHA | EOR # | LSR A | · | JMP abs | EOR abs | LSR abs | · |
| 5 | BVC rel | EOR (zp),Y | · | · | · | EOR zp,X | LSR zp,X | · | CLI | EOR abs,Y | · | · | · | EOR abs,X | LSR abs,X | · |
| 6 | RTS | ADC (zp,X) | · | · | · | ADC zp | ROR zp | · | PLA | ADC # | ROR A | · | JMP (abs) | ADC abs | ROR abs | · |
| 7 | BVS rel | ADC (zp),Y | · | · | · | ADC zp,X | ROR zp,X | · | SEI | ADC abs,Y | · | · | · | ADC abs,X | ROR abs,X | · |
| 8 | · | STA (zp,X) | · | · | STY zp | STA zp | STX zp | · | DEY | · | TXA | · | STY abs | STA abs | STX abs | · |
| 9 | BCC rel | STA (zp),Y | · | · | STY zp,X | STA zp,X | STX zp,Y | · | TYA | STA abs,Y | TXS | · | · | STA abs,X | · | · |
| A | LDY # | LDA (zp,X) | LDX # | · | LDY zp | LDA zp | LDX zp | · | TAY | LDA # | TAX | · | LDY abs | LDA abs | LDX abs | · |
| B | BCS rel | LDA (zp),Y | · | · | LDY zp,X | LDA zp,X | LDX zp,Y | · | CLV | LDA abs,Y | TSX | · | LDY abs,X | LDA abs,X | LDX abs,Y | · |
| C | CPY # | CMP (zp,X) | · | · | CPY zp | CMP zp | DEC zp | · | INY | CMP # | DEX | · | CPY abs | CMP abs | DEC abs | · |
| D | BNE rel | CMP (zp),Y | · | · | · | CMP zp,X | DEC zp,X | · | CLD | CMP abs,Y | · | · | · | CMP abs,X | DEC abs,X | · |
| E | CPX # | SBC (zp,X) | · | · | CPX zp | SBC zp | INC zp | · | INX | SBC # | NOP | · | CPX abs | SBC abs | INC abs | · |
| F | BEQ rel | SBC (zp),Y | · | · | · | SBC zp,X | INC zp,X | · | SED | SBC abs,Y | · | · | · | SBC abs,X | INC abs,X | · |

Per-opcode cycles, bytes and flags come next from Appendix B (one instruction per half page, PDF ~198–225).
 Each will get an exact table row (encoding, addressing mode, cycles, flags), as the 8080's §6.1.

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
- **Interrupt timing**, what MOS documents (confirmed §10, Hardware Manual §1.3.2.5 p.25, §1.4.1.2.9–10 p.38, page images):
  - **IRQ** is level-sensitive. The CPU is interrupted while `irq_n` = 0 and I = 0, after it "completes the instruction currently being executed", so the line must be held low until then. I is set "during the last cycle before the processor begins executing the interrupt software".
  - **NMI** "always interrupts the processor after it completes the instruction currently being executed". It's edge-triggered (a high-to-low transition), must stay low "for at least two clock cycles" to be recognised, and isn't recognised again until the line goes high and then low.
  - **Not documented by MOS** (in either 1976 manual, as far as read): the one-instruction IRQ delay after a taken branch without a page cross, an NMI arriving during a BRK's push cycles taking over its vector ("hijack"), and the priority when IRQ and NMI become pending at the same instruction boundary.
  - **Proposed *Decision*** for these three: they're **not specified**, and the §7 stimulus rule keeps tests out of them. `irq_n`/`nmi_n` change only at instruction boundaries (the edge that starts an opcode-fetch cycle, `sync` = 1), never while an interrupt sequence is running, and never both in the same boundary. The model and RTL then never have to agree on unspecified behaviour. Reopen it if a primary source turns up. Unlike decimal-mode N/V/Z, this restricts only *when* tests drive pins, and every program behaviour stays specified.
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
1. **Klaus Dormann's 6502 functional test**, `6502_functional_test.a65` (github.com/Klaus2m5/6502_65C02_functional_tests). **Licence checked** (2026-11-17, file header): "Copyright (C) 2012-2020 Klaus Dormann", **GNU GPL version 3 or (at your option) any later version**. It's fetched at test time, pinned by commit and sha256, never committed (rule 9), as for the 8080 exercisers.
   - Scope (header): "Tests documented behavior of the original NMOS 6502 only!", so 65C02/65816 opcodes are not tested. That matches §1.
   - Decimal mode (header): "Decimal ops will only be tested with valid BCD operands and N V Z flags will be ignored." So this test passes under **any** of the §6 decimal options (a)–(c). It has a build option to disable the decimal tests altogether.
   - The same repo has `6502_decimal_test.a65`, "Bruce Clark's code to accurately test decimal mode". That's the test that would check NMOS N/V/Z under option (a). **Licence checked** (header): "Written by Bruce Clark. This code is **public domain**." By default it compares only A and C. N, V and Z checks are switches (`chk_n`, `chk_v`, `chk_z`), and `cputype = 0` selects its NMOS 6502 flag prediction. Fetched at test time like the rest.
2. **Per-instruction test vectors with bus activity**: SingleStepTests `65x02` (github.com/SingleStepTests/65x02), directory `6502`. **Licence: MIT** (repo). The README says the tests "include bus activity" and were generated by an implementation that "has been verified by usage in an emulated machine". **Not verified against real hardware**, so they're a **cross-check, not ground truth**, in the same role as MAME. Where a vector disagrees with a spec rule taken from a MOS manual, the spec wins and the case is filed as an issue. Use only the 151 documented opcodes (§6 decision). [check: the per-cycle record format, and whether undocumented opcodes are mixed in].
3. **Example programs from the MOS Programming Manual**, typed in from the page images, expected values from the manual's text where printed.
4. **An independent existing 6502 emulator** for instruction-level comparison (Beru chooses, MAME's core first, licence recorded).

## 10. Datasheet check
Every [check] gets a line here with the page it was confirmed on. Both 1976 scans (bitsavers) have **no text layer**, so every check is read from page images (poppler, toolchain#35). Page offset: Programming Manual printed page *n* = PDF page *n* + 13 up to about p.92, and *n* + 16 by p.138 (unnumbered inserts), so check the printed number on each rendered page.
- [ ] §4 per-cycle table from Appendix A (PDF 168–182): A-1 to A-13 transcribed into §4.1 (single-byte; all read modes incl. abs,X/Y, zp,X/Y, (ind),Y; stores begun). Next: A-6 onward. "BAH + C" reading backed by A.3.6 (dummy read at uncarried BAH). ROR availability note (A-7) → revision decision in §1. A-8 to A-13 done: RMW double write, push/pull, JSR, BRK/interrupts, RTI, JMP, RTS, branches (uncarried first read on taken branches). **Appendix A complete.**
- [x] Opcode set: Appendix D (D-2 to D-5, page images) lists 151 documented opcodes, 56 mnemonics, 13 addressing modes; 105 bytes are "Future Expansion". ROR is listed (66/6A/6E/76/7E), consistent with the §1 revision decision. Counted by script from a transcription of all 256 entries.
- [x] §9 Dormann functional test licence: GPL-3.0-or-later (file header, read 2026-11-17); NMOS documented behaviour only; decimal with valid BCD only, N/V/Z ignored. Bruce Clark decimal test: public domain (header), N/V/Z checks optional with NMOS prediction. SingleStepTests 65x02: MIT, emulator-generated, not hardware-verified, so a cross-check only.
- [x] IRQ/NMI (Hardware Manual pp.25, 38, page images): IRQ level-sensitive and recognised after the current instruction completes; NMI edge-triggered, ≥ 2 cycles low, recognised after the current instruction; I set in the last cycle before the interrupt software. Branch delay, NMI-hijacks-BRK and IRQ/NMI priority are **not** documented, so §6 proposes not specifying them and keeping stimulus away.
- [x] RDY (Hardware Manual §1.4.1.2.8, p.37, page image; offset printed n = PDF n + 13): stops only read cycles; a write in progress completes, and the stop happens at the next read; change in φ1, recognised in the next φ2. Also p.32: "The address bus will always contain known data as detailed in Appendix A", the per-cycle table to read for §4.
- [x] I and D (§3.2–3.3, pp.26–27, page images): I changed only by BRK, CLI, PLP, RTI, SEI; D only by CLD, PLP, RTI, SED (so interrupts don't clear D); SED makes ADC/SBC decimal. Decimal ADC/SBC (§2.2.1.2–2.2.2, pp.13–14, page images): BCD result and C defined; **N/V/Z in decimal mode not stated anywhere in the manual**, so it's an open decision (§6).
- [x] Reset (§9.1–9.3, pp.125–127, page images): Read state while reset is low and until the vector is fetched; Example 9.1's 7-cycle start sequence (stack accesses are reads); the only automatic actions are I = 1 and PC ← vector; registers random. Open: minimum reset low time (Hardware Manual), S after the sequence (*Decision*: not compared).
- [x] Interrupt sequence (§9.5, Example 9.2, p.131, page image): 7 cycles as listed in §4. Cycle 2 forces a BRK, cycle 7 sets I, and the text says "the interrupt disable is turned on … automatically". So BRK sets I.
- [x] BRK (§9.11, p.144, page image): pushes PC + 2 and P, vector FFFE/FFFF, pushed B = 1 for BRK, 0 for IRQ, B is bit 4 (`AND #$10`). Open: B on PHP/NMI (I after BRK is resolved by p.131 above).
- [x] `JMP ($xxFF)` page wrap: §6.6 (p.92) is silent, but **§9.8.1, Example 9.6 "Illustration of JMP Indirect" (p.141, page image)** gives the cycle table: cycle 4 reads ADL at "IAH, IAL" while doing "Add 1 to IAL", and cycle 5 reads ADH at "IAH, IAL+1". The increment is to IAL alone, so the high-byte pointer stays in the same page. This is a primary-source basis for the wrap, read from the bus addresses, not stated as a caution.
