# Spec: Intel 8080 (Chip #2), DRAFT

Status: **DRAFT v0, not normative.** Written by Igris on 2026-11-14 so that it's reviewed by the time the 4004 is released. Nobody builds from this until (a) the 4004 is released (roadmap rule), (b) every **[check]** item is confirmed against the datasheet (§10), and (c) Sai signs it off. It then moves to `TuriChips/chip-8080`, the same way the 74181 and 4004 specs did.

Facts marked **[check]** are from memory of the 8080 documentation and must be read from the page before this is normative. Choices that are ours, not Intel's, are marked *Decision*.

Sources to read in §10:
- Intel, *8080 Microcomputer Systems User's Manual* (September 1975): instruction set, timing, pins, 8224 clock generator and 8228 system controller.
- Intel, *8080A/8080A-1/8080A-2 8-Bit N-Channel Microprocessor* datasheet.

## 1. Scope
- The **8080 CPU**, cycle-accurate at its pins: every state (T1–T5, TW, THOLD, TWH) of every machine cycle (M1–M5) is specified at the pins (§4), like the 4004's §4.
- **Not in scope:** electrical behaviour (+12/+5/−5 V supplies, the non-overlapping two-phase clock's timing), the 8224 clock generator and the 8228 system controller as chips. The status byte that the 8228 latches is on the data bus at SYNC and is specified at the pins, so a test can decode it. A minimal `i8080_system` (CPU, RAM, a status latch, and a simple I/O port model) is in scope for the acceptance tests.
- Logic convention: positive logic, 1 = true, as for the 4004. The 8080's pins are active-high except where noted [check: WR is active-low on the real part].
- Clock: *Decision.* One rising-edge model clock `clk` per clock state (one φ1/φ2 period = one T state). The real 2 MHz two-phase clock is noted, not modelled.

## 2. Pins (top module `i8080`)
The real 40-pin package [check pinout] has a bidirectional 8-bit data bus. As for the 4004, it is split into `d_in`/`d_out`/`d_oe`, with no tri-states in RTL. The 16-bit address bus is also tri-stated on the real part (during HOLD), so it gets `a_oe`.

| Signal | Dir | Width | Meaning [check all] |
|--------|-----|-------|---------|
| `clk` | in | 1 | Model clock, one per T state |
| `reset` | in | 1 | RESET, active high, synchronous. Clears PC; see §5 |
| `a` | out | 16 | A15–A0 |
| `a_oe` | out | 1 | 0 while the address bus is floated (HOLD acknowledged) |
| `d_in` | in | 8 | D7–D0 driven by memory or I/O |
| `d_out` | out | 8 | D7–D0 driven by the CPU (status byte at T1/T2, write data) |
| `d_oe` | out | 1 | 1 when the CPU drives the data bus |
| `sync` | out | 1 | SYNC: high in T1 of every machine cycle; the status byte is on D7–D0 |
| `dbin` | out | 1 | DBIN: CPU is reading the data bus (T2, T3 of read cycles) |
| `wr_n` | out | 1 | WR (active low): data on the bus is valid for memory or I/O write |
| `ready` | in | 1 | READY: 0 inserts TW wait states after T2 |
| `wait_o` | out | 1 | WAIT: CPU is in a wait state |
| `hold` | in | 1 | HOLD: request to float the buses |
| `hlda` | out | 1 | HLDA: hold acknowledged |
| `int_req` | in | 1 | INT: interrupt request |
| `inte` | out | 1 | INTE: interrupt enable flip-flop |

**Status byte** (on `d_out` while `sync` = 1) [check bit order]: D0 INTA, D1 WO (active low), D2 STACK, D3 HLTA, D4 OUT, D5 M1, D6 INP, D7 MEMR.

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

## 5. Reset [check]
RESET held for at least 3 clock periods. Clears PC and INTE, and the instruction register. The other registers and flags are unaffected on the real part. *Decision:* tests must hold reset ≥ 3 clocks and must not read A, B–L, SP or F before writing them.

## 6. Instructions (normative once checked)
244 opcodes [check] in the groups below, each to get an exact table like the 4004's §6, with S/Z/AC/P/CY effects per instruction:
- Data transfer: MOV, MVI, LXI, LDA, STA, LHLD, SHLD, LDAX, STAX, XCHG.
- Arithmetic: ADD, ADC, SUB, SBB, ADI, ACI, SUI, SBI, INR, DCR, INX, DCX, DAD, DAA.
- Logical: ANA, XRA, ORA, CMP, ANI, XRI, ORI, CPI, RLC, RRC, RAL, RAR, CMA, CMC, STC.
- Branch: JMP, Jcc, CALL, Ccc, RET, Rcc, RST, PCHL.
- Stack, I/O, machine control: PUSH, POP (incl. PSW), XTHL, SPHL, IN, OUT, EI, DI, HLT, NOP.

Known quirks to pin down exactly (each needs a source):
- **AC after ANA/ANI**: set to the OR of bit 3 of the two operands on the 8080 [check]. This differs from the 8085.
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
Not started. Every [check] above gets a line here with the page it was confirmed on, as in the 4004's §10.
