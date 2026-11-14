# Spec: Intel 8080 (Chip #2), DRAFT

Status: **DRAFT v0, not normative.** Written by Igris on 2026-11-14 so that it's reviewed by the time the 4004 is released. Nobody builds from this until (a) the 4004 is released (roadmap rule), (b) every **[check]** item is confirmed against the datasheet (§10), and (c) Sai signs it off. It then moves to `TuriChips/chip-8080`, the same way the 74181 and 4004 specs did.

Facts marked **[check]** are from memory of the 8080 documentation and must be read from the page before this is normative. Choices that are ours, not Intel's, are marked *Decision*.

Sources to read in §10:
- Intel, *8080 Microcomputer Systems User's Manual* (September 1975): instruction set, timing, pins, 8224 clock generator and 8228 system controller.
- Intel, *8080A/8080A-1/8080A-2 8-Bit N-Channel Microprocessor* datasheet.

## 1. Scope
- The **8080 CPU**, cycle-accurate at its pins: every state (T1–T5, TW, THOLD, TWH) of every machine cycle (M1–M5) is specified at the pins (§4), like the 4004's §4.
- **Not in scope:** electrical behaviour (+12/+5/−5 V supplies, the non-overlapping two-phase clock's timing), the 8224 clock generator and the 8228 system controller as chips. The status byte that the 8228 latches is on the data bus at SYNC and is specified at the pins, so a test can decode it. A minimal `i8080_system` (CPU, RAM, a status latch, and a simple I/O port model) is in scope for the acceptance tests.
- Logic convention: positive logic, 1 = true, as for the 4004. The 8080's pins are active-high except WR, which is active low (User's Manual p.5-14; modelled as `wr_n`).
- Clock: *Decision.* One rising-edge model clock `clk` per clock state (one φ1/φ2 period = one T state). The real 2 MHz two-phase clock is noted, not modelled.

## 2. Pins (top module `i8080`)
The real 40-pin package (pinout in §10) has a bidirectional 8-bit data bus. As for the 4004, it is split into `d_in`/`d_out`/`d_oe`, with no tri-states in RTL. The 16-bit address bus is also tri-stated on the real part (during HOLD), so it gets `a_oe`.

| Signal | Dir | Width | Meaning (from User's Manual p.5-14 unless marked [check]) |
|--------|-----|-------|---------|
| `clk` | in | 1 | Model clock, one per T state |
| `reset` | in | 1 | RESET, active high, synchronous. Clears PC, INTE and HLDA; see §5 |
| `a` | out | 16 | A15–A0 |
| `a_oe` | out | 1 | 0 while the address bus is floated (HOLD acknowledged) |
| `d_in` | in | 8 | D7–D0 driven by memory or I/O |
| `d_out` | out | 8 | D7–D0 driven by the CPU (status byte at T1/T2, write data) |
| `d_oe` | out | 1 | 1 when the CPU drives the data bus |
| `sync` | out | 1 | SYNC: high in T1 of every machine cycle; the status byte is on D7–D0 |
| `dbin` | out | 1 | DBIN: CPU is reading the data bus (T2, T3 of read cycles) |
| `wr_n` | out | 1 | WR (active low): data on the bus is valid for memory or I/O write |
| `ready` | in | 1 | READY: while low after an address is sent, the CPU stays in WAIT (TW) states (p.5-14). Exact sampling state [check] |
| `wait_o` | out | 1 | WAIT: CPU is in a wait state |
| `hold` | in | 1 | HOLD: request to float the buses. Recognised only in HALT, or in T2/TW with READY active (p.5-14) |
| `hlda` | out | 1 | HLDA: hold acknowledged. Starts at T3 of a memory-read or input cycle, or the clock period after T3 of a write or output cycle (p.5-14) |
| `int_req` | in | 1 | INT: recognised at the end of the current instruction or while halted; ignored in HOLD or when INTE = 0 (p.5-14) |
| `inte` | out | 1 | INTE flip-flop: set by EI, reset by DI, by RESET, and at T1 of the M1 cycle in which an interrupt is accepted (p.5-14) |

**Status byte** (on `d_out` while `sync` = 1, confirmed §10): D0 INTA, D1 WO (active low), D2 STACK, D3 HLTA, D4 OUT, D5 M1, D6 INP, D7 MEMR.

## 3. Programmer's model [check]
| Name | Width | Reset value | Notes |
|------|-------|-------------|-------|
| `A` | 8 | not reset (*Decision*: tests must not depend on it; the RTL may clear it) | Accumulator |
| `B C D E H L` | 8 each | not reset (same *Decision*) | Pairs BC, DE, HL (`H`, `B`, `D` high) |
| `SP` | 16 | not reset (same *Decision*) | Stack pointer |
| `PC` | 16 | 0 | Program counter |
| `F` | 8 | not reset | Flags `S Z 0 AC 0 P 1 CY` from bit 7 to bit 0, as pushed by PUSH PSW (bits 5 and 3 = 0, bit 1 = 1) |
| `INTE` | 1 | 0 | Interrupt enable |

Memory: 64 KiB, byte addressed. I/O: 256 input and 256 output ports, the port number is put on both halves of the address bus [check].

## 4. Machine cycle timing (normative once checked)
To be written, at the same level as the 4004's §4: per machine-cycle type (instruction fetch, memory read, memory write, stack read, stack write, input, output, interrupt acknowledge, halt acknowledge, interrupt acknowledge while halted), and per T state, the values of `a`, `a_oe`, `d_out`, `d_oe`, `sync`, `dbin`, `wr_n`, `wait_o`, `hlda`. Instructions take 4, 5, 7, 10, 11, 13, 16 or 18 states [check: 5 for INX/DCX, MOV r,r; 18 for XTHL]. READY sampled in T2 [check], HOLD sampled in T2 [check], INT sampled at the end of the last state of each instruction [check].

## 5. Reset
RESET held for at least 3 clock periods restores PC to 0; it "has no effect on status flags, or on any of the processor's working registers (accumulator, registers, or stack pointer)", which stay indeterminate until the program sets them (User's Manual p.2-13, confirmed §10). RESET also resets INTE and HLDA (p.5-14). The instruction register on reset: [check]. *Decision:* tests hold reset ≥ 3 clocks and must not read A, B–L, SP or F before writing them; the RTL may clear them.

## 6. Instructions (normative once checked)
244 opcodes [check] in the groups below, each to get an exact table like the 4004's §6, with S/Z/AC/P/CY effects per instruction:
- Data transfer: MOV, MVI, LXI, LDA, STA, LHLD, SHLD, LDAX, STAX, XCHG.
- Arithmetic: ADD, ADC, SUB, SBB, ADI, ACI, SUI, SBI, INR, DCR, INX, DCX, DAD, DAA.
- Logical: ANA, XRA, ORA, CMP, ANI, XRI, ORI, CPI, RLC, RRC, RAL, RAR, CMA, CMC, STC.
- Branch: JMP, Jcc, CALL, Ccc, RET, Rcc, RST, PCHL.
- Stack, I/O, machine control: PUSH, POP (incl. PSW), XTHL, SPHL, IN, OUT, EI, DI, HLT, NOP.

Known quirks to pin down exactly (each needs a source):
- **AC after logical instructions** (confirmed §10): ANA/ANI set **AC = (bit 3 of A) OR (bit 3 of the operand)**, before the AND, and clear CY (8080/8085 Assembly Language Programming Manual p.1-11: "The 8080 logical AND instructions set the flag to reflect the logical OR of bit 3 of the values involved"; on the 8085 AND always sets AC, so the 8080 rule is the one we follow). ORA, XRA, XRI clear both CY and AC (same manual, ch.3); ORI the same [check]. The 1975 User's Manual (p.4-8) only says "standard rules" for these, which is why the second source is needed.
- **CY after SUB/CMP**: set on borrow (inverse of the 4004's SUB convention). This needs an explicit statement.
- **DAA**: the exact two-step rule, including AC and CY in and out.
- **Undocumented opcodes** (08, 10, 18, 20, 28, 30, 38 as NOP; CB as JMP; D9 as RET; DD, ED, FD as CALL) [check]. *Proposed decision*: specify them as the real part behaves if the source is solid, else "execute as documented NOP-like; tests must not depend on it", as the 4004's FE/FF.

## 7. System for tests (reduced detail)
`i8080_system`: one `i8080`, 64 KiB RAM loaded from a `$readmemh` image, a status latch (what the 8228 does), and an I/O model for a console port, so CP/M-style test programs can print. The bus resolution and `bus_conflict` flag are the same idea as the 4004's `mcs4_system`.

## 8. Behaviours to test (draft)
| ID | Behaviour |
|----|-----------|
| C1 | Every opcode: registers, memory and all five flags exactly per §6 |
| C2 | Pin timing per §4 for every machine-cycle type, including the status byte at SYNC |
| C3 | READY / wait states, HOLD / HLDA, at every legal point |
| C4 | Interrupts: EI's one-instruction delay [check], RST via the interrupt-acknowledge cycle, INT while halted |
| C5 | DAA and AC in every case |
| C6 | Reset |
| C7 | No X/Z on any output; no bus conflict |
| C8 | Random programs vs Beru's reference model on every pin and state |

## 9. Acceptance tests (software not written by this team), candidates
1. **8080 instruction exercisers** that are widely used to validate 8080 emulators (e.g. the "8080 Instruction Exerciser" family and CPU test programs that run under a minimal CP/M BDOS stub). The licence and provenance of each must be checked before use. Same rule as Busicom: fetched at test time, never committed (rule 9).
2. **Example programs from the 8080 User's Manual**, typed in, with expected results from the manual's text.
3. **Instruction-level comparison against an independent existing 8080 emulator** (Beru chooses, like MAME for the 4004).

## 10. Datasheet check
Source read: Intel *8080 Microcomputer Systems User's Manual*, September 1975 (98-153B, scan with text layer), read 2026-11-14 by Igris. Page numbers are the manual's printed numbers.
- [x] Status byte bit assignment: D0 INTA, D1 WO (active low: 0 = write/output), D2 STACK, D3 HLTA, D4 OUT, D5 M1, D6 INP, D7 MEMR (Table 2-1, p.2-6).
- [x] Reset: ≥ 3 clock periods, PC to 0, no effect on flags, A, B–L or SP (p.2-13).
- [x] Reset also resets INTE and HLDA; "flags, accumulator, stack pointer, and registers are not cleared" (p.5-14).
- [ ] Reset effect on the instruction register.
- [x] Pin functions (8080A functional pin definition, p.5-14): WR active low; READY low → WAIT; HOLD recognised in HALT or in T2/TW with READY active; HLDA from T3 (read/input) or the period after T3 (write/output); INTE reset by RESET and at T1 of M1 when an interrupt is accepted; INT recognised at the end of an instruction or while halted, not in HOLD or with INTE = 0.
- [~] Pinout (p.5-14 figure, OCR; pins 31 and 34 to be confirmed on the page image): 1 A10, 2 GND, 3 D4, 4 D5, 5 D6, 6 D7, 7 D3, 8 D2, 9 D1, 10 D0, 11 −5V, 12 RESET, 13 HOLD, 14 INT, 15 φ2, 16 INTE, 17 DBIN, 18 WR, 19 SYNC, 20 +5V, 21 HLDA, 22 φ1, 23 READY, 24 WAIT, 25 A0, 26 A1, 27 A2, 28 +12V, 29 A3, 30 A4, 31 A5, 32 A6, 33 A7, 34 A8, 35 A9, 36 A15, 37 A12, 38 A13, 39 A14, 40 A11. Reference only; tests bind to the RTL port names in §2.
- [x] AC after ANA/ANI: not stated in the User's Manual (p.4-8 says "standard rules"); confirmed from the second source below.

Second source: Intel *8080/8085 Assembly Language Programming Manual* (9800301D, May 1981, scan with text layer), read 2026-11-14 by Igris.
- [x] ANA/ANI: AC = OR of bit 3 of the two operands; 8085 differs (always sets AC) (p.1-11).
- [x] ORA r/M, XRA M, XRI: CY and AC reset to 0 (ch.3, near pp.3-39 and 3-66/3-67; exact page to be re-read from the page image).
- [ ] ORI: same rule expected, not yet read.
- [ ] Exact READY sampling state, instruction state counts, DAA rule, I/O port number on both address halves (p.5-14 only says A15–A0 "denotes the I/O device number for up to 256 input and 256 output devices").
- [ ] Undocumented opcodes: not expected in Intel's manuals at all; needs a decision on sources (§6).
