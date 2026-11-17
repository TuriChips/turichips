# Spec: MOS 6502 (Chip #3)

Status: **v1, normative. Signed off by Sai on 2026-11-17 (turichips#32)**, including the §6 decimal-mode decision (option (a)). Written by Igris from 2026-11-16, after the 8080's release, for roadmap chip #3. It moves to `TuriChips/chip-6502`, the same way the 4004 and 8080 specs did. Two small [check]s stay open and don't block the build: the cycle in which S.O. updates V (§2), and the uncarried-dummy-read reading (§4.1), which C8 and SingleStepTests cross-check anyway.

Facts marked **[check]** are from memory and must be read from the page (as page images where the scan's text is unreliable) before this is normative. Choices that are ours, not MOS's, are marked *Decision*.

Sources for §10 (bitsavers, fetched to a scratch dir, never committed):
- MOS Technology, *MCS6500 Microcomputer Family Hardware Manual*, 6500-10A, January 1976 (pins, timing, interrupts, reset).
- MOS Technology, *MCS6500 Microcomputer Family Programming Manual*, 6500-50A, January 1976 (instructions, addressing modes, flags, decimal mode).

## 1. Scope
- The **NMOS 6502 CPU**, cycle-accurate at its pins: every clock cycle's address, data direction, R/W and SYNC is specified (§4), including the "dummy" bus cycles the real part makes. Those are visible at the pins, and real software and hardware depend on some of them.
- **Revision** (*Decision*): the **post-June-1976 NMOS 6502, with ROR**. The Hardware Manual (A-7) notes "The ROR instruction will be available on MCS650X microprocessors after June, 1976". So earlier parts lack ROR, which is why A.1's 1976 list has no ROR A. We specify the version with ROR (ROR A, and ROR in every memory mode) because that's the 6502 later used in the Atari 2600 and NES (roadmap chips #5 and #11).
- **Not in scope:** the 65C02 and other CMOS variants, the 6507/6510 package variants (the Atari 2600's 6507 is chip #5's business), electrical timing, the two-phase clock's waveforms.
- Logic convention: positive logic. Active-low pins keep a `_n` suffix (`irq_n`, `nmi_n`, `res_n`), as the 8080 did with `wr_n`.
- Clock: *Decision.* One rising-edge model clock `clk` per φ2 cycle. Every 6502 cycle is one bus access, read or write (confirmed: Appendix A lists an address, data and R/W for every Tn, and Hardware Manual p.32 says "The address bus will always contain known data").

## 2. Pins (top module `m6502`)
| Signal | Dir | Width | Meaning (each row cites its Hardware Manual page, or is marked) |
|--------|-----|-------|---------|
| `clk` | in | 1 | Model clock, one per cycle |
| `res_n` | in | 1 | RESET, active low |
| `a` | out | 16 | A15–A0, driven in every cycle |
| `d_in` | in | 8 | D7–D0 from memory or I/O |
| `d_out` | out | 8 | D7–D0 driven by the CPU in write cycles |
| `d_oe` | out | 1 | 1 in write cycles (split bus, no tri-states, as for the 4004 and 8080) |
| `rw` | out | 1 | R/W: 1 = read, 0 = write |
| `sync` | out | 1 | SYNC: 1 for the whole of an opcode-fetch cycle (Hardware Manual §1.4.2.3, p.44). With `rdy` = 0 in that cycle the CPU "will stop in its current state", keeping `sync` = 1, until `rdy` = 1 (single-instruction step) |
| `rdy` | in | 1 | RDY: 0 delays the current cycle, **only if it's a read** (Hardware Manual §1.4.1.2.8, p.37: "will not stop the processor in a cycle in which a WRITE operation is being performed … will execute that cycle and will then stop in the next READ cycle (R/W = 1)"). The CPU repeats the stopped read cycle with the same address while `rdy` = 0 |
| `irq_n` | in | 1 | Maskable interrupt, level-sensitive, gated by the I flag |
| `nmi_n` | in | 1 | Non-maskable interrupt, edge-sensitive (falling edge) |
| `so_n` | in | 1 | Set Overflow: "sets the overflow flag on a negative transition", "should not be used in normal applications" (p.44). *Decision*: held at 1 in C8; one directed C-test drives a falling edge at an instruction boundary and checks V = 1 afterwards. The exact cycle of the V update is [check] |

## 3. Programmer's model
| Name | Width | Reset value | Notes |
|------|-------|-------------|-------|
| `A`, `X`, `Y` | 8 each | **not reset** (p.126: "internal registers may be initialized to any random condition") | *Decision*: unreset, with a C8 preamble as for the 8080 |
| `S` | 8 | **not initialised** (p.127: the only automatic reset actions are setting I and loading PC; programs start with `LDX #n; TXS`). The reset sequence reads at {01,S}, {01,S−1}, {01,S−2} (Example 9.1); whether S is left decremented by 3 is not stated, so *Decision*: S after reset is **not compared**, and the C8 preamble sets it | Stack in page 1, address `{01, S}` |
| `PC` | 16 | from the reset vector FFFC/FFFD | |
| `P` | 8 | **I = 1** after reset (p.127: "turn on the interrupt disable bit"); the others not reset (the same page lists no other automatic action) | `N V 1 B D I Z C`, bit 5 reads 1 when pushed. **B exists only in the pushed byte**: 1 from BRK (p.144, Appendix B-8) and PHP (§6 *Decision*, matching Dormann), 0 from IRQ (p.144) and NMI (§6 *Decision*) |

Vectors: NMI FFFA/FFFB, RESET FFFC/FFFD, IRQ and BRK FFFE/FFFF.

## 4. Cycle timing (normative once checked)
**Source:** Hardware Manual **Appendix A, "Summary of Single Cycle Execution"** (PDF pages 168 to the end, A-1 onward), which "contains an outline of the data on both the address bus and the data bus for each cycle of the various processor instructions". It restates on A-1 that the processor "will not stop in any cycle where R/W is a 0". It is being transcribed into this section page by page. To be written as a total table, like the 8080's: for each addressing mode × instruction class (read, write, read-modify-write, branch, stack, jump, interrupt sequence), every cycle's `a`, `rw`, `sync`, and `d_out` when writing. This is where most 6502 bugs live, so every cycle must be pinned, including the dummy ones (done: every cycle is transcribed from Appendix A in §4.1, with page refs):
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

**A.1 Single-byte instructions, 2 cycles** (A-2): ASL A, CLC, CLD, CLI, CLV, DEX, DEY, INX, INY, LSR A, NOP, ROL A, SEC, SED, SEI, TAX, TAY, TSX, TXA, TXS, TYA. (ROR A isn't listed because "The ROR instruction will be available on MCS650X microprocessors after June, 1976" (A-7). It behaves exactly like the other accumulator-mode shifts, 2 cycles (Appendix B-23), per the §1 revision decision.)
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

The zero-page pointer arithmetic stays in page 00. Appendix A writes the high byte of every zero-page access as a literal **00** ("00, BAL + X", "00, BAL + X + 1"), and A.4.3 says outright "BAL + X (without carry)". So BAL + X + 1 = FF + 1 wraps to 00 within page zero.

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

\* Same footnote and the same reading of "BAH + C" as A.2.5. IAL + 1 stays in page 00 ("00, IAL + 1", the same literal-00 rule), so IAL = FF reads BAH from 0000.

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

A.5.1 PHP, PHA (3): "Stack Ptr." = {01, S}. **S points at the next free byte** (Programming Manual §8.13, p.123: each stack store "automatically decrements the stack pointer, thereby leaving the stack pointer pointing at the next open memory byte", and each stack read "adds 1 to the current value of the stack pointer and reads … 0100 plus the stack pointer"). So a push writes {01, S} then S − 1, and a pull does S + 1 then reads {01, S}.
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

So a taken branch's first extra cycle reads at the **uncarried** target, the same pattern as the indexed reads above. T2's high byte is PC+2's page: the manual writes T2 as "PC + 2 + offset (w/o carry)" and T3 as "with carry", and they differ only when the carry would change the page.

**Appendix A is fully transcribed.** §4.0 now states the per-cycle comparison rule. Interrupt timing is in §6.

## 5. Reset
While `res_n` = 0 the CPU is "guaranteed to be in a Read state" (`rw` = 1), and after release it stays in Read until it has fetched the vector (p.126). Then the 7-cycle sequence in §4, and the first opcode fetch in cycle 8. Minimum low time for `res_n`: not stated in either manual (§1.4.1.2.11, p.40 gives only the behaviour). *Decision*: tests hold `res_n` = 0 for **at least 8 cycles**, and the behaviour for shorter pulses isn't specified. While `res_n` = 0, "writing from the microprocessor is inhibited" (p.40), which confirms `rw` = 1 (§5). p.40 says that after release the CPU "will delay 6 cycles and then fetch the new program count vectors". Example 9.1's per-cycle table (vector reads in cycles 6–7) governs the exact cycles.
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

### 6.1 Instructions (Programming Manual Appendix B, "Instruction List Alphabetic by Mnemonic", B-3 onward = PDF 200 onward, page images)
Cycle counts per addressing mode follow §4.1 (Appendix A). **Where Appendix B's cycle column and Appendix A's tables disagree, Appendix A governs**, because it lists every cycle, and the disagreement is noted below. "+p" = one more cycle if the indexed address crosses a page (reads only; stores and RMW always take the long count, §4.1).

| Mnemonic | Operation | N Z C I D V | Modes (opcode, cycles) |
|----------|-----------|-------------|------------------------|
| ADC | A + M + C → A, C | ✓ ✓ ✓ – – ✓ | # 69 2 · zp 65 3 · zp,X 75 4 · abs 6D 4 · abs,X 7D 4+p · abs,Y 79 4+p · (zp,X) 61 6 · (zp),Y 71 5+p |
| AND | A ∧ M → A | ✓ ✓ – – – – | # 29 2 · zp 25 3 · zp,X 35 4 · abs 2D 4 · abs,X 3D 4+p · abs,Y 39 4+p · (zp,X) 21 6 · (zp),Y 31 5+p (B-3 prints "5" without the asterisk; A.2.7 gives 6 on a page cross, so A governs) |

| ASL | C ← [7…0] ← 0 | ✓ ✓ ✓ – – – | A 0A 2 · zp 06 5 · zp,X 16 6 · abs 0E 6 · abs,X 1E 7 |
| BCC | branch if C = 0 | – – – – – – | rel 90 2 (+1 taken, +2 taken to another page) |
| BCS | branch if C = 1 | – – – – – – | rel B0 2 (+1 / +2) |
| BEQ | branch if Z = 1 | – – – – – – | rel F0 2 (+1 / +2) |
| BIT | A ∧ M; Z ← (A ∧ M = 0); **N ← M7, V ← M6** | M7 ✓ – – – M6 | zp 24 3 · abs 2C 4 |
| BMI | branch if N = 1 | – – – – – – | rel 30 2 (+1 / +2) |

| BNE | branch if Z = 0 | – – – – – – | rel D0 2 (+1 / +2) |
| BPL | branch if N = 0 | – – – – – – | rel 10 2 (+1 / +2) |
| BRK | forced interrupt: PC + 2 ↓, P ↓, PC ← (FFFE) | – – – **1** – – | impl 00 7. "A BRK command cannot be masked by setting I" (B-8) |
| BVC | branch if V = 0 | – – – – – – | rel 50 2 (+1 / +2) |
| BVS | branch if V = 1 | – – – – – – | rel 70 2 (+1 / +2) |
| CLC | 0 → C | – – 0 – – – | impl 18 2 |

| CLD | 0 → D | – – – – 0 – | impl D8 2 |
| CLI | 0 → I | – – – 0 – – | impl 58 2 |
| CLV | 0 → V | – – – – – 0 | impl B8 2 |
| CMP | A − M (flags only) | ✓ ✓ ✓ – – – | # C9 2 · zp C5 3 · zp,X D5 4 · abs CD 4 · abs,X DD 4+p · abs,Y D9 4+p · (zp,X) C1 6 · (zp),Y D1 5+p |
| CPX | X − M (flags only) | ✓ ✓ ✓ – – – | # E0 2 · zp E4 3 · abs EC 4 |
| CPY | Y − M (flags only) | ✓ ✓ ✓ – – – | # C0 2 · zp C4 3 · abs CC 4 |

| DEC | M − 1 → M | ✓ ✓ – – – – | zp C6 5 · zp,X D6 6 · abs CE 6 · abs,X DE 7 |
| DEX | X − 1 → X | ✓ ✓ – – – – | impl CA 2 |
| DEY | Y − 1 → Y | ✓ ✓ – – – – | impl 88 2 |
| EOR | A ⊻ M → A | ✓ ✓ – – – – | # 49 2 · zp 45 3 · zp,X 55 4 · abs 4D 4 · abs,X 5D 4+p · abs,Y 59 4+p · (zp,X) 41 6 · (zp),Y 51 5+p |
| INC | M + 1 → M | ✓ ✓ – – – – | zp E6 5 · zp,X F6 6 · abs EE 6 · abs,X FE 7 |
| INX | X + 1 → X | ✓ ✓ – – – – | impl E8 2 |

| INY | Y + 1 → Y | ✓ ✓ – – – – | impl C8 2 |
| JMP | (PC+1) → PCL, (PC+2) → PCH | – – – – – – | abs 4C 3 · (abs) 6C 5 (page wrap, §6) |
| JSR | PC + 2 ↓, (PC+1) → PCL, (PC+2) → PCH | – – – – – – | abs 20 6 |
| LDA | M → A | ✓ ✓ – – – – | # A9 2 · zp A5 3 · zp,X B5 4 · abs AD 4 · abs,X BD 4+p · abs,Y B9 4+p · (zp,X) A1 6 · (zp),Y B1 5+p |
| LDX | M → X | ✓ ✓ – – – – | # A2 2 · zp A6 3 · **zp,Y** B6 4 · abs AE 4 · **abs,Y** BE 4+p |
| LDY | M → Y | ✓ ✓ – – – – | # A0 2 · zp A4 3 · zp,X B4 4 · abs AC 4 · abs,X BC 4+p |

| LSR | 0 → [7…0] → C | **0** ✓ ✓ – – – | A 4A 2 · zp 46 5 · zp,X 56 6 · abs 4E 6 · abs,X 5E 7 |
| NOP | none | – – – – – – | impl EA 2 |
| ORA | A ∨ M → A | ✓ ✓ – – – – | # 09 2 · zp 05 3 · zp,X 15 4 · abs 0D 4 · abs,X 1D 4+p · abs,Y 19 4+p · (zp,X) 01 6 · (zp),Y 11 5+p (B-20 prints "5" without the asterisk, as for AND; A governs) |
| PHA | A ↓ | – – – – – – | impl 48 3 |
| PHP | P ↓ (B = 1 and bit 5 = 1 in the pushed byte, §6 *Decision*) | – – – – – – | impl 08 3 |
| PLA | A ↑ | ✓ ✓ – – – – | impl 68 4 |

| PLP | P ↑ | from stack | impl 28 4 |
| ROL | C ← [7…0] ← C | ✓ ✓ ✓ – – – | A 2A 2 · zp 26 5 · zp,X 36 6 · abs 2E 6 · abs,X 3E 7 |
| ROR | C → [7…0] → C | ✓ ✓ ✓ – – – | A 6A 2 · zp 66 5 · zp,X 76 6 · abs 6E 6 · abs,X 7E 7 (B-23 repeats "available … after June, 1976"; §1 revision decision) |
| RTI | P ↑, PC ↑ | from stack | impl 40 6 |
| RTS | PC ↑, PC + 1 → PC | – – – – – – | impl 60 6 |
| SBC | A − M − C̄ → A (C̄ = borrow) | ✓ ✓ ✓ – – ✓ | # E9 2 · zp E5 3 · zp,X F5 4 · abs ED 4 · abs,X FD 4+p · abs,Y F9 4+p · (zp,X) E1 6 · (zp),Y F1 5+p |
| SEC | 1 → C | – – 1 – – – | impl 38 2 |

| SED | 1 → D | – – – – 1 – | impl F8 2 |
| SEI | 1 → I | – – – 1 – – | impl 78 2 |
| STA | A → M | – – – – – – | zp 85 3 · zp,X 95 4 · abs 8D 4 · abs,X 9D 5 · abs,Y 99 5 · (zp,X) 81 6 · (zp),Y 91 6 |
| STX | X → M | – – – – – – | zp 86 3 · **zp,Y** 96 4 · abs 8E 4 |
| STY | Y → M | – – – – – – | zp 84 3 · zp,X 94 4 · abs 8C 4 |
| TAX | A → X | ✓ ✓ – – – – | impl AA 2 |
| TAY | A → Y | ✓ ✓ – – – – | impl A8 2 |
| TSX | S → X | ✓ ✓ – – – – | impl BA 2 |
| TXA | X → A | ✓ ✓ – – – – | impl 8A 2 |
| TXS | X → S | – – – – – – (**no flags**) | impl 9A 2 |
| TYA | Y → A | ✓ ✓ – – – – | impl 98 2 |

All 56 instructions transcribed (Appendix B, B-3 to B-29). Cross-checked by script: the opcodes in this table are exactly the 151 of the §6.0 map (Appendix D). Branch cycle notes on B-4 to B-6 say "+1 if branch occurs to same page, +2 if … to different page" (B-5 says "next page", the same meaning), matching A.5.8.
 Each will get an exact table row (encoding, addressing mode, cycles, flags), as the 8080's §6.1.

Quirks that must each be pinned to a source line before C1 is written:
- **`JMP ($xxFF)`** fetches the high byte from `$xx00`, not `$(xx+1)00` (confirmed §10: Programming Manual Example 9.6, p.141, fetches ADH from address "IAH, IAL+1" after "Add 1 to IAL", an 8-bit add to the low byte with no carry into IAH). Bus cycles: 1 opcode at PC, 2 IAL at PC+1, 3 IAH at PC+2, 4 ADL at {IAH, IAL}, 5 ADH at {IAH, IAL+1 mod 256}, then the next opcode fetch at {ADH, ADL}.
- **Which instructions change I and D** (confirmed §10, Programming Manual §3.2–3.3, pp.26–27): I only by BRK, CLI, PLP, RTI, SEI (and the interrupt/reset sequences, p.127/131); **D only by CLD, PLP, RTI, SED**. So on the NMOS part **an interrupt or BRK does not clear D**, and D is random after reset (p.127 lists I as the only flag reset sets). A test or the C8 preamble must clear or set D explicitly.
- **Decimal mode (D = 1)**, what the manual says (confirmed §10, Programming Manual §2.2.1.2–2.2.2, pp.13–14): with D = 1, ADC and SBC produce packed-BCD results (Example 2.12: 79 + 14 = 93), and **C** tells the user whether the result "exceeds … 99 decimal" (ADC). For SBC, C = 1 means no borrow (A − M − C̄). **The manual says nothing about N, V or Z after a decimal operation.**
  - ***Decision* (Sai, 2026-11-17, turichips#32: option (a)): decimal-mode N, V and Z follow the real NMOS 6502**, for **every** operand byte, valid BCD or not. The MOS manual is silent, so the rule is taken from the secondary source that's also our acceptance test: Bruce Clark's `6502_decimal_test.a65` (public domain, §9), its `cputype = 0` prediction (routines `ADD`, `SUB1`, `A6502`, `S6502`, read 2026-11-17). With `c` the carry in, D = 1:
    - **ADC.**
      1. `lo = A[3:0] + M[3:0] + c`. If `lo ≥ $0A`: `lo = (lo + 6) & $0F` and `hc = 1`, else `hc = 0`.
      2. `t = {A[7:4], lo[3:0]} + B' + hc`, an ordinary 8-bit binary add with carry in `hc`, where `B' = {M[7:4], 0000}` if `hc = 0` and `B' = {M[7:4], 1111}` if `hc = 1` (so the half carry adds `$10`; these are Clark's exact operands, `N2H,x`). **N = bit 7 of `t[7:0]`**, and **V = this add's two's-complement overflow**.
      3. If the add carried out of bit 7, or `t[7:0] ≥ $A0`: `t = t + $60`. **A = `t[7:0]`**, and **C = 1** if the carry out of step 2 or step 3 was 1.
      4. **Z = 1 if the *binary* sum `(A + M + c) mod 256` is 0**, not the BCD result. (Example: `$99 + $01`, c = 0, gives A = `$00`, C = 1, Z = 0.)
    - **SBC.** **N, V, Z and C are exactly those of the binary SBC** (`A − M − (1 − c)`). Only A is decimal:
      1. `lo = A[3:0] − M[3:0] − (1 − c)`. If `lo < 0`: `lo = (lo − 6) & $0F` and `hb = 1`, else `hb = 0`.
      2. `t = {A[7:4], lo[3:0]} − B' − hb`, where `B' = {M[7:4], 0000}` if `hb = 0` and `B' = {M[7:4], 1111}` if `hb = 1` (so the half borrow subtracts `$10`). If this borrowed (`t < 0`): `t = t − $60`.
      3. **A = `t[7:0]`**.
    - Tests: C5 checks this with Clark's test, every operand pair and both carries, A, N, V, Z and C all compared (§9). C8's generator may set D = 1 and use any operand.
- **The B flag and BRK** (confirmed §10, Programming Manual §9.11, p.144): BRK pushes the address of the **second byte after BRK** (PC + 2) and P, then loads PC from FFFE/FFFF. In the pushed P, **B (bit 4, the manual's `AND #$10`) is 1 for BRK and 0 for an IRQ**. **BRK sets I** (confirmed §10): an interrupt is serviced by **forcing a BRK** (Example 9.2, p.131, cycle 2: "Force a BRK Instruction"), and that shared sequence does "Vector Low → PCL and Set I" in cycle 7. The text adds that "the interrupt disable is turned on at this point by the microprocessor automatically". **Stated directly in Appendix B-8**: BRK's flag row is `N Z C I D V = – – – 1 – –`, so BRK sets I. p.144's "changes no values in either the registers or the flags" therefore means "none other than I". No decision is needed. **B for PHP and NMI** (*Decision*, the manual doesn't say): PHP "transfers the contents of the processor status register **unchanged** to the stack" (§8.11, p.122). But B isn't a stored bit (only the pushed byte carries it, p.144), so "unchanged" doesn't define it. We specify: **PHP pushes B = 1** (a software push, like BRK), and **NMI pushes B = 0** (a hardware interrupt, like IRQ). Bit 5 is 1 in every pushed P. This matches the acceptance test: Dormann's functional test defines `fao equ break+reserv ;bits always on after PHP, BRK` and compares pushed bytes with B and bit 5 set ("flags off except break (pushed by sw) + reserved"), read 2026-11-17.
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
| C5 | Decimal mode per §6: A, C, and NMOS N/V/Z, for all 256 × 256 operands and both carries (Clark's test, §9) |
| C6 | Reset sequence and vectors |
| C7 | No X/Z, no bus conflict, with the positive-case test (8080 lesson) |
| C8 | Random programs vs Beru's reference model, ≥ 10,000 × 1,000 instructions, pins every cycle |

## 9. Acceptance test candidates (licences to be checked before use, as for the 8080)
1. **Klaus Dormann's 6502 functional test**, `6502_functional_test.a65` (github.com/Klaus2m5/6502_65C02_functional_tests). **Licence checked** (2026-11-17, file header): "Copyright (C) 2012-2020 Klaus Dormann", **GNU GPL version 3 or (at your option) any later version**. It's fetched at test time, pinned by commit and sha256, never committed (rule 9), as for the 8080 exercisers.
   - Scope (header): "Tests documented behavior of the original NMOS 6502 only!", so 65C02/65816 opcodes are not tested. That matches §1.
   - Decimal mode (header): "Decimal ops will only be tested with valid BCD operands and N V Z flags will be ignored." So this test passes under **any** of the §6 decimal options (a)–(c). It has a build option to disable the decimal tests altogether.
   - The same repo has `6502_decimal_test.a65`, "Bruce Clark's code to accurately test decimal mode". It's the C5 acceptance test for the §6 decision (option (a)). We build it with `cputype = 0`, `vld_bcd = 0`, and `chk_a`, `chk_n`, `chk_v`, `chk_z`, `chk_c` all = 1. **Licence checked** (header): "Written by Bruce Clark. This code is **public domain**." By default it compares only A and C. N, V and Z checks are switches (`chk_n`, `chk_v`, `chk_z`), and `cputype = 0` selects its NMOS 6502 flag prediction. Fetched at test time like the rest.
2. **Per-instruction test vectors with bus activity**: SingleStepTests `65x02` (github.com/SingleStepTests/65x02), directory `6502`. **Licence: MIT** (repo). The README says the tests "include bus activity" and were generated by an implementation that "has been verified by usage in an emulated machine". **Not verified against real hardware**, so they're a **cross-check, not ground truth**, in the same role as MAME. Where a vector disagrees with a spec rule taken from a MOS manual, the spec wins and the case is filed as an issue. Format (the `6502` directory README, read 2026-11-17): **one JSON file per opcode, named by hex** (e.g. `a9.json` = LDA #), with **10,000 tests per file**. Each test has `initial` and `final` state (pc, s, a, x, y, p, and `ram` as `[address, value]` pairs; "any address not listed must not be accessed") and **`cycles`: one `[address, value, "read"|"write"]` per cycle**. That maps onto §4.0's `a`, `rw` and data per cycle. `sync` isn't recorded, so it's checked by §4.0's own rule (1 exactly on T0). **We use exactly the 151 files of the §6.0 map, by name.** Whether the directory also has files for undocumented bytes doesn't matter, because they're never loaded.
3. **Example programs from the MOS Programming Manual**, typed in from the page images, expected values from the manual's text where printed.
4. **An independent existing 6502 emulator** for instruction-level comparison (Beru chooses, MAME's core first, licence recorded).

## 10. Datasheet check
Every [check] gets a line here with the page it was confirmed on. Both 1976 scans (bitsavers) have **no text layer**, so every check is read from page images (poppler, toolchain#35). Page offset: Programming Manual printed page *n* = PDF page *n* + 13 up to about p.92, and *n* + 16 by p.138 (unnumbered inserts), so check the printed number on each rendered page.
- [ ] §4 per-cycle table from Appendix A (PDF 168–182): A-1 to A-13 transcribed into §4.1 (single-byte; all read modes incl. abs,X/Y, zp,X/Y, (ind),Y; stores begun). Next: A-6 onward. "BAH + C" reading backed by A.3.6 (dummy read at uncarried BAH). ROR availability note (A-7) → revision decision in §1. A-8 to A-13 done: RMW double write, push/pull, JSR, BRK/interrupts, RTI, JMP, RTS, branches (uncarried first read on taken branches). **Appendix A complete.**
- [ ] Appendix B (B-3 onward, PDF 200+): **All 56 instructions** transcribed into §6.1 (B-3 to B-29; opcode set cross-checked by script against Appendix D; ORA (zp),Y has the same missing asterisk as AND; JSR "PC + 2 ↓" on B-17 agrees with the RTS table; BRK's flag row I = 1 on B-8 confirms BRK sets I; AND (zp),Y "5" without asterisk vs A.2.7, Appendix A governs). Done.
- [x] Stack pointer semantics (§8.13, p.123): S points at the next free byte; push = write then decrement, pull = increment then read.
- [x] B on PHP/NMI: PHP pushes P "unchanged" (§8.11, p.122), so B isn't defined there. *Decision*: PHP B = 1, NMI B = 0; matches Dormann's `fao` ("bits always on after PHP, BRK").
- [x] Opcode set: Appendix D (D-2 to D-5, page images) lists 151 documented opcodes, 56 mnemonics, 13 addressing modes; 105 bytes are "Future Expansion". ROR is listed (66/6A/6E/76/7E), consistent with the §1 revision decision. Counted by script from a transcription of all 256 entries.
- [x] §9 Dormann functional test licence: GPL-3.0-or-later (file header, read 2026-11-17); NMOS documented behaviour only; decimal with valid BCD only, N/V/Z ignored. Bruce Clark decimal test: public domain (header), N/V/Z checks optional with NMOS prediction. SingleStepTests 65x02: MIT, emulator-generated, not hardware-verified, so a cross-check only. Format confirmed: per-opcode files, 10,000 tests, per-cycle [address, value, read/write]; we load only the 151 documented opcodes' files.
- [x] SYNC, S.O., RES (Hardware Manual pp.40, 44): SYNC high for the opcode-fetch cycle, RDY in that cycle holds with SYNC high; S.O. falling edge sets V, not for normal use; reset inhibits writes, vector fetch after the start cycles; no minimum reset time given (*Decision*: ≥ 8 cycles in tests). NMI during IRQ servicing (p.40 event 12): NMI taken regardless of I, IRQ resumes after.
- [x] IRQ/NMI (Hardware Manual pp.25, 38, page images): IRQ level-sensitive and recognised after the current instruction completes; NMI edge-triggered, ≥ 2 cycles low, recognised after the current instruction; I set in the last cycle before the interrupt software. Branch delay, NMI-hijacks-BRK and IRQ/NMI priority are **not** documented, so §6 proposes not specifying them and keeping stimulus away.
- [x] RDY (Hardware Manual §1.4.1.2.8, p.37, page image; offset printed n = PDF n + 13): stops only read cycles; a write in progress completes, and the stop happens at the next read; change in φ1, recognised in the next φ2. Also p.32: "The address bus will always contain known data as detailed in Appendix A", the per-cycle table to read for §4.
- [x] I and D (§3.2–3.3, pp.26–27, page images): I changed only by BRK, CLI, PLP, RTI, SEI; D only by CLD, PLP, RTI, SED (so interrupts don't clear D); SED makes ADC/SBC decimal. Decimal ADC/SBC (§2.2.1.2–2.2.2, pp.13–14, page images): BCD result and C defined; **N/V/Z in decimal mode not stated anywhere in the manual**, so it was a decision: option (a), NMOS N/V/Z per Clark's test (§6), Sai 2026-11-17.
- [x] Reset (§9.1–9.3, pp.125–127, page images): Read state while reset is low and until the vector is fetched; Example 9.1's 7-cycle start sequence (stack accesses are reads); the only automatic actions are I = 1 and PC ← vector; registers random. Open: minimum reset low time (Hardware Manual), S after the sequence (*Decision*: not compared).
- [x] Interrupt sequence (§9.5, Example 9.2, p.131, page image): 7 cycles as listed in §4. Cycle 2 forces a BRK, cycle 7 sets I, and the text says "the interrupt disable is turned on … automatically". So BRK sets I.
- [x] BRK (§9.11, p.144, page image): pushes PC + 2 and P, vector FFFE/FFFF, pushed B = 1 for BRK, 0 for IRQ, B is bit 4 (`AND #$10`). Open: B on PHP/NMI (I after BRK is resolved by p.131 above).
- [x] `JMP ($xxFF)` page wrap: §6.6 (p.92) is silent, but **§9.8.1, Example 9.6 "Illustration of JMP Indirect" (p.141, page image)** gives the cycle table: cycle 4 reads ADL at "IAH, IAL" while doing "Add 1 to IAL", and cycle 5 reads ADH at "IAH, IAL+1". The increment is to IAL alone, so the high-byte pointer stays in the same page. This is a primary-source basis for the wrap, read from the bus addresses, not stated as a caution.
