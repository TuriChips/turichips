# Spec: Zilog Z80 (Chip #4) — draft v0, not normative

Status: **draft.** Nothing here is normative until Sai signs off. Lines marked [check] still need a page reference in §10.

## 1. Scope and sources

**What we rebuild:** the original NMOS Zilog Z80 CPU (1976), as documented by Zilog in 1977. One 40-pin CPU; no peripherals (PIO, CTC, SIO, DMA are separate chips).

**Primary sources** (Zilog, both © 1977, fetched from the bitsavers mirror for reading, not committed):
- **TM**: *Z80-CPU Z80A-CPU Technical Manual*, 03-0029-01. 83 pages, with a text layer (page images still checked for tables). Chapters: 2 architecture, 3 pins, 4 CPU timing, 5 instruction set, 6 flags, 7 op codes and execution times, 8 interrupt response, 11 electrical, 12 instruction summary.
- **PM**: *Z80-Assembly Language Programming Manual* (January 1978 printing). 315 pages, per-instruction descriptions with flags and timing.

As with the 6502, the manuals win. Secondary sources (emulators, test-vector sets) are cross-checks only, and each use is named where it's used.

**Proposed scope decisions** (each to be confirmed before sign-off):
- **Documented instructions only.** Behaviour of opcodes the 1977 manuals don't list (e.g. the `DD CB`/`FD CB` register-copy forms, `SLL`, IXH/IXL halves) is not specified, and tests don't execute them, as with the 6502's 105 undocumented opcodes.
- **Undocumented flag bits** (bits 3 and 5 of F, the "X"/"Y" flags; TM §6.0 shows them as "X", unused) are **not compared**. This matters for the acceptance test choice (§9): `zexall` checks them, `zexdoc` doesn't.
- **Refresh (R register and RFSH):** in scope. R's low 7 bits increment per M1, and the refresh address appears on A0–A6 in T3–T4 of M1 (TM §3.0, §4.0) [check].
- **Electrical timing (TM §11)** is out of scope: we model cycles, not nanoseconds.

## 2. Pins (TM §3.0, Figure 3.0-1)

Active-low pins keep an `_n` suffix (`m1_n`, `mreq_n`, …), as the 8080 and 6502 did.

| Pin | Dir | Width | Meaning (TM §3.0, quoted or close paraphrase) |
|-----|-----|-------|-----------------------------------------------|
| `a` | out (tri-state) | 16 | Address bus. I/O uses the low 8 bits for up to 256 ports. "During refresh time, the lower 7 bits contain a valid refresh address." |
| `d_in` / `d_out` / `d_oe` | in / out / out | 8 / 8 / 1 | Data bus, tri-state bidirectional, split as for the 8080 and 6502 |
| `m1_n` | out | 1 | "The current machine cycle is the OP code fetch cycle." Asserted for **each** opcode byte of a 2-byte opcode (prefixes CB, DD, ED, FD). Also asserted with `iorq_n` for an interrupt acknowledge |
| `mreq_n` | out (tri-state) | 1 | The address bus holds a valid memory address |
| `iorq_n` | out (tri-state) | 1 | The low half of the address bus holds a valid I/O address. Also asserted with `m1_n` for interrupt acknowledge. "I/O operations never occur during M1 time" |
| `rd_n` | out (tri-state) | 1 | The CPU wants to read from memory or I/O |
| `wr_n` | out (tri-state) | 1 | The data bus holds valid data to be written |
| `rfsh_n` | out | 1 | The low 7 bits of the address bus are a refresh address, and `mreq_n` is a refresh read |
| `halt_n` | out | 1 | The CPU executed HALT and waits for NMI, or for INT with interrupts enabled. "While halted, the CPU executes NOP's to maintain memory refresh activity" |
| `wait_n` | in | 1 | Memory/I/O not ready. "The CPU continues to enter wait states for as long as this signal is active" |
| `int_n` | in | 1 | Maskable interrupt, honoured "at the end of the current instruction" if the IFF is enabled **and `busrq_n` is not active**. Three modes (TM §5.4) |
| `nmi_n` | in | 1 | Negative-edge triggered, higher priority than INT, always recognised at the end of the current instruction, restarts at **0066H**. "Continuous WAIT cycles can prevent the current instruction from ending", and "a BUSRQ will override a NMI" |
| `reset_n` | in | 1 | Forces PC to 0 and: disables the IFF, I = 00H, R = 00H, interrupt mode 0. "During reset time, the address bus and data bus go to a high impedance state and all control output signals go to the inactive state" |
| `busrq_n` | in | 1 | Requests the buses and tri-state controls float "as soon as the current CPU machine cycle is terminated" |
| `busak_n` | out | 1 | The buses and tri-state controls are floating |
| `clk` | in | 1 | Single-phase clock |

## 3. Open decisions (to settle before this spec can be normative)

1. **How to model half-cycle edges.** TM §4.0 [check] has MREQ, RD and WR changing on the clock's **falling** edge within a T state (e.g. MREQ falls half-way through T1). Options: (a) a model clock at 2× the T-state rate, so every half T state is one model cycle; (b) one model cycle per T state, comparing each pin's value as it stands at the end of that T state, with the half-cycle detail stated as "not compared". The 8080 used per-T-state comparison. **Leaning (a)**, since Z80 bus timing is defined by the half-cycle edges. To be decided after reading TM §4.0 in full.
2. **Wait sampling point.** TM says WAIT is sampled in T2 of each cycle [check]; it needs the exact edge in the chosen model.
3. **Interrupt mode 0** puts an arbitrary instruction on the bus. The proposal is to test it only with RST n (single byte), as the 8080 spec did.
4. **Undocumented behaviour:** confirm §1's scope list with Sai, especially the X/Y flags (it decides zexdoc vs zexall, §9).
5. **Reset:** the minimum `reset_n` low time and the first fetch cycle (TM §8/§4 [check]), with the same "which cycles are compared" table as the 6502's §5.

## 4–8. Timing, reset, instructions, interrupts, tests
To be written from TM §4–8 and PM, in the 6502 spec's layout: a total per-cycle table, the flags per instruction, the interrupt modes, and the behaviour list C1–C8.

## 9. Acceptance test candidates (licences to check before use)
1. **zexdoc** (Frank D. Cringle's Z80 instruction exerciser, documented flags only), the Z80 counterpart of 8080EXM. It's fetched at test time and never committed. Licence to read from its header (GPL, as remembered; **not yet checked**).
2. **zexall**: the same, including the undocumented X/Y flags. Only if §1's flag decision changes.
3. **Per-instruction vectors with bus activity**: SingleStepTests `z80` set, a cross-check only, as for the 6502.
4. **Examples from the Zilog manuals** (TM §10, the PM).

## 10. Datasheet check
Every [check] gets a line here with the page it was confirmed on.
- [x] Pin list and functions (TM §3.0, pp.7–9, from the text layer; the page image is still to be compared for OCR errors): table in §2.
