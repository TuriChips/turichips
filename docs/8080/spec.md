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
To be written, at the same level as the 4004's §4: per machine-cycle type (instruction fetch, memory read, memory write, stack read, stack write, input, output, interrupt acknowledge, halt acknowledge, interrupt acknowledge while halted), and per T state, the values of `a`, `a_oe`, `d_out`, `d_oe`, `sync`, `dbin`, `wr_n`, `wait_o`, `hlda`. Instructions take 4, 5, 7, 10, 11, 13, 16, 17 or 18 states. From the User's Manual instruction summary: INX/DCX 5, DAD 10, SHLD/LHLD 16, CALL 17, Ccc 11/17, Rcc 5/11, XTHL 18, DAA 4 (confirmed §10). The full per-opcode table gets transcribed from that summary. READY sampled in T2 [check], HOLD sampled in T2 [check], INT sampled at the end of the last state of each instruction [check].


**Confirmed so far (User's Manual §2, pp.2-6 to 2-10), in our one-clock-per-state model:**

| Cycle kind | T1 | T2 | TW (while READY = 0) | T3 |
|------------|----|----|----------------------|----|
| all | `sync` = 1, `d_oe` = 1, `d_out` = status byte (§2), `a` = address, stable from T1 (p.2-6) | `sync` = 0 | `wait_o` = 1 | |
| read (fetch, memory read, stack read, input) | as above | `d_oe` = 0 (φ2 in T2 clears the status off the data lines, p.2-8); `dbin` = 1 (DBIN starts at φ2 in T2, p.2-8) | `d_oe` = 0, `dbin` = 1 | `d_oe` = 0; input data **sampled in T3** (p.2-8); `dbin` = 1 (*Decision*: the real DBIN ends at φ2 within T3; at one clock per state we keep it 1 for all of T3, so the sample point is covered) |
| write (memory write, stack write, output) | as above | `d_oe` = 1, `d_out` = **output data**, replacing status at φ2 of T2 (p.2-9) | `d_oe` = 1, data held; `wr_n` = 0 | `d_oe` = 1, data held; `wr_n` = 0 (WR falls at the first φ1 after T2 and rises at the start of the state after T3, p.2-10) |

- IN/OUT: the 8-bit port number is duplicated on both halves of `a`, so `a` = `{port, port}` (ALP manual p.1-15: "IN 5 latches … 0000 0101 0000 0101"; p.3-42).
- READY and HOLD must be stable during T2 or TW (User's Manual data sheet note 11/12, p.5-17), which supports the stimulus rule in §7.
- **READY and HOLD are sampled in T2** (and in each TW for READY); T2 is also where the CPU checks for halt (Table 2-2, p.2-10). With the §7 stimulus rule, a test changes them only on the edge starting T1 or TW.
- **T4 and T5** are internal-only states, skipped when an instruction doesn't need them (p.2-10). The real part puts "the contents of the internal bus during T4 and T5 … at the data bus … for testing purposes only" (p.2-20, note 3). *Decision:* in T4/T5, `d_oe` and `d_out` are **not compared**, because we don't specify the internal bus, and `i8080_system` must not drive the bus then (no DBIN). `sync` = 0, `dbin` = 0, `wr_n` = 1 in T4/T5. `a` in T4/T5: **held** at the cycle's address (Figure 2-11, p.2-14: A15–0 solid at PC from T1 through T4 of M1), so compared like T1–T3.
- Every cell with `d_oe` = 0 or `a_oe` = 0: `d_out` or `a` respectively is **not compared**. `d_oe`, `a_oe`, `sync`, `dbin`, `wr_n`, `wait_o`, `hlda`, `inte` are compared in every state.
- **Interrupt acknowledge cycle** (p.2-11): an enabled INT sets the internal interrupt latch in the last state of the current instruction, so the instruction always completes. The next cycle is like an M1 fetch, with status M1 = 1 **and** INTA = 1 (D0). `a` = PC in T1, but **PC is not incremented**. External logic puts the interrupt instruction on the bus for T3 (`i8080_system`: RST n, §7). INTE is reset at T1 of that cycle (p.5-14).
- **Hold** (p.2-13): HLDA rises at the start of T3 of a read or input cycle, otherwise at the start of the state after T3. The address and data lines float shortly after the next φ2, which is within that same state. *Decision* (one clock per state): `hlda` = 1, `a_oe` = 0, `d_oe` = 0 from that state on. If the cycle needs T4/T5, the CPU runs through them internally while held, then stops at the end of the machine cycle. When HOLD falls, `hlda` = 0 at the next state boundary, and the CPU resumes with the next machine cycle.
- **Halt** (p.2-13): after HLT, the CPU enters the halt state (TWH) after T2 of the next machine cycle, whose status has HLTA = 1. It leaves only by: RESET → T1 with PC = 0; HOLD → hold state, and back to halt when HOLD falls; or an interrupt with INTE = 1 → T1 of an interrupt-acknowledge cycle at the next state boundary. With INTE = 0 when the halt is entered, only RESET leaves it. In TWH (Figure 2-11, p.2-14): `wait_o` = 1 from the first TWH until the halt is left; `dbin` = 0; the address and data buses are drawn dashed. *Decision:* `a_oe` = 0 and `d_oe` = 0 in TWH, so `a`/`d_out` aren't compared. That reads Intel's dashed lines as floating, the same convention as the hold figures [check against the figure legend if one exists].
- §4 now has every cell type covered at the level of the manual's text and Figures 2-5 to 2-12. Before sign-off, the per-cycle table gets written out in full, one row per machine-cycle type × state, like the 4004's §4.
## 5. Reset
RESET held for at least 3 clock periods restores PC to 0; it "has no effect on status flags, or on any of the processor's working registers (accumulator, registers, or stack pointer)", which stay indeterminate until the program sets them (User's Manual p.2-13, confirmed §10). RESET also resets INTE and HLDA (p.5-14). The instruction register on reset: [check]. *Decision:* tests hold reset ≥ 3 clocks and must not read A, B–L, SP or F before writing them; the RTL may clear them.

**Pins while `reset` = 1** (*Decision*, as for the 4004): `a_oe` = 0, `d_oe` = 0, `sync` = 0, `dbin` = 0, `wr_n` = 1, `wait_o` = 0, `hlda` = 0, `inte` = 0. Nothing else is compared while `reset` = 1. Comparison starts at the first T1 after `reset` falls, which is the M1 of an instruction fetch from 0000. Reset in the middle of an instruction or a hold abandons it: the M-cycle and T-state counters and the instruction register are cleared, so the first cycle after reset is always an M1 fetch [check against the real part; if the manual is silent, this stays a *Decision*].

**Unreset registers in random tests** (*Decision*, Beru's option (b)): A, B–L, SP and F stay unreset, as on the real part. Every C8 program starts with a fixed preamble that writes all of them before anything reads them: `LXI SP,nnnn; LXI B; LXI D; LXI H; PUSH H; POP PSW; MVI A` (POP PSW sets F). The model starts comparing register-dependent results only after the preamble. The preamble's exact bytes go in `tests/random/` and are referenced here when written.

## 6. Instructions (normative once checked)
244 opcodes [check] in the groups below, each to get an exact table like the 4004's §6, with S/Z/AC/P/CY effects per instruction:
- Data transfer: MOV, MVI, LXI, LDA, STA, LHLD, SHLD, LDAX, STAX, XCHG.
- Arithmetic: ADD, ADC, SUB, SBB, ADI, ACI, SUI, SBI, INR, DCR, INX, DCX, DAD, DAA.
- Logical: ANA, XRA, ORA, CMP, ANI, XRI, ORI, CPI, RLC, RRC, RAL, RAR, CMA, CMC, STC.
- Branch: JMP, Jcc, CALL, Ccc, RET, Rcc, RST, PCHL.
- Stack, I/O, machine control: PUSH, POP (incl. PSW), XTHL, SPHL, IN, OUT, EI, DI, HLT, NOP.

Flag rules every opcode table row follows (to become per-opcode lines in the §6 tables):
- P = 1 when the result has an even number of 1 bits. Z = result is 0. S = result bit 7.
- INR/DCR: Z, S, P, AC from the result; **CY unchanged**.
- DAD: **only CY** changes (carry out of bit 15).
- CMP/CPI: flags exactly as SUB/SUI with the same operands; A unchanged. CY = 1 means borrow (A < operand, unsigned).
- SUB/SBB/SUI/SBI: CY = 1 on borrow. AC for subtraction [check: the 8080 computes it from the two's-complement addition `A + ~op + 1`; pin down from a source].
- Rotates (RLC, RRC, RAL, RAR): only CY changes.
- INX/DCX, MOV, MVI, LXI, loads/stores, XCHG, XTHL, SPHL, PCHL: no flags.

Known quirks to pin down exactly (each needs a source):
- **AC after logical instructions** (confirmed §10): ANA/ANI set **AC = (bit 3 of A) OR (bit 3 of the operand)**, before the AND, and clear CY (8080/8085 Assembly Language Programming Manual p.1-11: "The 8080 logical AND instructions set the flag to reflect the logical OR of bit 3 of the values involved"; on the 8085 AND always sets AC, so the 8080 rule is the one we follow). ORA, XRA, XRI clear both CY and AC (same manual, ch.3), and ORI too (User's Manual p.4-9: "The CY and AC flags are cleared"). The 1975 User's Manual (p.4-8) only says "standard rules" for these, which is why the second source is needed.
- **CY after SUB/CMP**: set on borrow (inverse of the 4004's SUB convention). This needs an explicit statement.
- **DAA** (User's Manual p.4-8, ALP manual p.3-19; 4 states): step 1, if `A[3:0] > 9` or AC = 1, add 6 to A, and **AC = carry out of bit 3** of that addition, else AC = 0 [check: AC when step 1 doesn't add]. Step 2, if `A[7:4] > 9` (after step 1) or CY = 1, add 6 to `A[7:4]`. **CY = 1 if that addition carries out of bit 7** (the ALP example: 93+08 → 9B → A1 → 01, CY = AC = 1). *Decision* (not stated by either manual): CY = CY_in OR carry-out, so a CY that was already 1 stays 1. A set CY means the decimal result already exceeds 99. Z, S, P from the final A.
- **Undocumented opcodes** (*Decision*, 2026-11-14): the 12 bytes that Intel's manuals don't define (08, 10, 18, 20, 28, 30, 38, CB, D9, DD, ED, FD) are **not tested**, and C8's generator excludes them, as for the 4004's 01–0F/FE/FF. The RTL may implement the commonly reported behaviour (08–38 as NOP, CB as JMP, D9 as RET, DD/ED/FD as CALL). That isn't required, because we have no primary source for it. If a primary-quality source turns up before the RTL is written, this can be reopened by a spec PR.

## 7. System for tests (reduced detail)
`i8080_system`: one `i8080`, 64 KiB RAM loaded from a `$readmemh` image, a status latch (what the 8228 does), and an I/O model for a console port, so CP/M-style test programs can print. The bus resolution and `bus_conflict` flag are the same idea as the 4004's `mcs4_system`.

**Interrupt acknowledge in `i8080_system`** (*Decision*): during an INTA cycle (status D0 = 1) the system puts a single RST n opcode on the bus, with n (0–7) from a test input `int_vector[2:0]`. CALL via INTA is not used in this project. INT while halted: the halt is left through the INTA M1 cycle exactly as from a running instruction, timing per §4 when written.

**Input stimulus rule** (*Decision*, the same idea as the 4004's TEST rule): tests change `ready`, `hold` and `int_req` only on the clock edge that **starts** a T1 or TW state, never mid-state. The exact sampling edges (READY at the end of T2/TW, HOLD at the end of T2 or in halt, INT at the end of the last state of each instruction and only if INTE = 1 at that edge) are [check] and get pinned in §4 with page references. The stimulus rule makes any edge within the state equivalent for a correct design.

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
- [x] ORI: CY and AC cleared (User's Manual p.4-9).
- [x] DAA steps (User's Manual p.4-8) and its flags: AC from step 1, CY from step 2's carry (ALP manual p.3-19 example). CY_in kept: *Decision*, not in either manual.
- [x] State counts (instruction summary table): INX/DCX 5, DAD 10, SHLD/LHLD 16, CALL 17, Ccc 11/17, Rcc 5/11, XTHL 18, DAA 4. Remaining opcodes to transcribe into §6.
- [x] I/O port number on both address halves (ALP p.1-15, p.3-42).
- [x] SYNC marks T1 only, with status on D0–D7 in the same interval (p.2-6). Output data replaces status at T2 and is held to the end of the cycle; WR is low from the state after T2 through T3 (p.2-9, 2-10). Input data sampled in T3 (p.2-8).
- [x] READY and HOLD sampled in T2 (Table 2-2, p.2-10; stable during T2 or TW, p.5-17). DBIN from φ2 in T2 to φ2 in T3 (p.2-8).
- [x] T4/T5 internal only; internal bus contents appear on the data bus for testing (p.2-20, note 3), hence not compared.
- [x] Interrupt acknowledge cycle (p.2-11), hold entry and exit (p.2-13), halt entry and the three exits (p.2-13).
- [x] `a` held through T4 of M1; in TWH WAIT = 1, DBIN = 0, buses dashed (Figure 2-11, p.2-14, page image rendered with poppler, toolchain#35).
- [x] Halt flow (Figure 2-12, p.2-14) matches the three exits in §4. (p.5-14 only says A15–A0 "denotes the I/O device number for up to 256 input and 256 output devices").
- [x] Undocumented opcodes: decided not tested (§6), since neither Intel manual defines them.
- [ ] Reset in mid-instruction / mid-hold and the instruction register (§5 *Decision* until a source says otherwise).
- [ ] AC for SUB/SBB/CMP.
