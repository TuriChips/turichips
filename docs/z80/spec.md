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

1. **How to model half-cycle edges.** *Proposed in §4.0: option (a), one model clock per half T state.* TM §4.0 [check] has MREQ, RD and WR changing on the clock's **falling** edge within a T state (e.g. MREQ falls half-way through T1). Options: (a) a model clock at 2× the T-state rate, so every half T state is one model cycle; (b) one model cycle per T state, comparing each pin's value as it stands at the end of that T state, with the half-cycle detail stated as "not compared". The 8080 used per-T-state comparison. **Leaning (a)**, since Z80 bus timing is defined by the half-cycle edges. To be decided after reading TM §4.0 in full.
2. **Wait sampling point.** TM says WAIT is sampled in T2 of each cycle [check]; it needs the exact edge in the chosen model.
3. **Interrupt mode 0** puts an arbitrary instruction on the bus. The proposal is to test it only with RST n (single byte), as the 8080 spec did.
4. **Undocumented behaviour:** confirm §1's scope list with Sai, especially the X/Y flags (it decides zexdoc vs zexall, §9).
5. **Reset:** the minimum `reset_n` low time and the first fetch cycle (TM §8/§4 [check]), with the same "which cycles are compared" table as the 6502's §5.

## 4. Timing (TM §4.0; normative once checked)

### 4.0 The model clock (*Decision* proposed, settles §3 item 1 as option (a))
TM §4.0 times every machine cycle (M cycle) in T states, one clock period Φ each, and **several pins change on the falling edge of Φ, half-way through a T state**. Figure 4.0-1, page image p.12: MREQ and RD go active "one half clock time later" than the address, and in Figure 4.0-2 (p.13) WR falls mid-T2 and goes inactive "one half T state before the address and data bus contents are changed". A per-T-state model can't show those edges, so:

- **One model clock = one half T state.** Each T state *Tn* is two model cycles: ***Tn*H** (Φ high, the first half, starting at Φ's rising edge) and ***Tn*L** (Φ low, starting at Φ's falling edge). A model edge is a Φ edge.
- Every pin is compared **in every half**, at the value it holds through that half (as the 6502's §4.0, with a half in place of a cycle).
- Inputs are sampled at the edge the manual names: **WAIT at the falling edge that starts T2L and each TwL** (TM p.12, "with the falling edge of Φ"); **opcode data at the rising edge that starts T3** in M1 (TM p.12).
- Below, "falls mid-T1" means the pin changes at the edge that starts T1L.

### 4.1 M1, opcode fetch (Figure 4.0-1, p.12), 4 T states plus waits
| half | `a` | `m1_n` | `mreq_n` | `rd_n` | `rfsh_n` | notes |
|------|-----|--------|----------|--------|----------|-------|
| T1H | PC | **0** | 1 | 1 | 1 | PC on the bus "at the beginning of the M1 cycle" |
| T1L | PC | 0 | **0** | **0** | 1 | MREQ and RD "one half clock time later" |
| T2H | PC | 0 | 0 | 0 | 1 | |
| T2L | PC | 0 | 0 | 0 | 1 | WAIT sampled at this edge; if 0, Tw follows (TwH/TwL repeat this row, WAIT sampled again at each TwL) |
| T3H | refresh address | **1** | **1** | **1** | **0** | opcode taken from `d_in` at the edge that starts T3H; "this same edge is used … to turn off the RD and MREQ signals" |
| T3L | refresh address | 1 | **0** | 1 | 0 | refresh MREQ; "a RD signal is not generated during refresh time" |
| T4H | refresh address | 1 | 0 | 1 | 0 | |
| T4L | refresh address | 1 | **1** | 1 | 0 | MREQ rises mid-T4 (Figure 4.0-1 and 4.0-1A) |
| next T1H | — | — | — | — | **1** | RFSH ends with T4 |

Refresh address: the low 7 bits are R's low 7 bits (TM §3.0). What drives A7–A15 during refresh is [check] (TM §2/§5 on the I register).

### 4.2 Memory read and write, not M1 (Figure 4.0-2, p.13), 3 T states plus waits
| half | `a` | `mreq_n` | `rd_n` (read) | `wr_n` (write) | `d_oe` (write) |
|------|-----|----------|---------------|----------------|----------------|
| T1H | address | 1 | 1 | 1 | 0 |
| T1L | address | **0** | **0** | 1 | **1** (DATA OUT starts mid-T1 in the figure) [check] |
| T2H | address | 0 | 0 | 1 | 1 |
| T2L | address | 0 | 0 | **0** | 1 |
| T3H | address | 0 | 0 | 0 | 1 |
| T3L | address | **1** | **1** | **1** | 1 |
| next T1H | next address | | | | 0 |

- WAIT is sampled at the edge that starts T2L, and Tw states are inserted between T2 and T3, as in M1 (Figure 4.0-2A).
- **Read data sampling edge [check]:** the text says MREQ and RD are "used the same as in the fetch cycle". The figure's IN window sits at the end of T3H, and MREQ and RD rise at the start of T3L, so the proposal is that read data is taken at the edge that starts T3L. That has to be confirmed against TM §11's timing table before it's normative.
- `m1_n` = 1 and `rfsh_n` = 1 throughout.

I/O cycles (Figure 4.0-3), bus request (4.0-4), interrupt acknowledge (4.0-5, 4.0-6) and HALT exit (4.0-7) are next.

## 5–8. Reset, instructions, interrupts, tests
To be written from TM §5–8 and PM, in the 6502 spec's layout: the flags per instruction, the interrupt modes, and the behaviour list C1–C8.

## 9. Acceptance test candidates (licences to check before use)
1. **zexdoc** (Frank D. Cringle's Z80 instruction exerciser, documented flags only), the Z80 counterpart of 8080EXM. It's fetched at test time and never committed. Licence to read from its header (GPL, as remembered; **not yet checked**).
2. **zexall**: the same, including the undocumented X/Y flags. Only if §1's flag decision changes.
3. **Per-instruction vectors with bus activity**: SingleStepTests `z80` set, a cross-check only, as for the 6502.
4. **Examples from the Zilog manuals** (TM §10, the PM).

## 10. Datasheet check
Every [check] gets a line here with the page it was confirmed on.
- [x] Pin list and functions (TM §3.0, pp.7–9, from the text layer; the page image is still to be compared for OCR errors): table in §2.
- [x] M1 and memory read/write timing (TM §4.0, Figures 4.0-1, 4.0-1A, 4.0-2, page images pp.12–13): §4.1, §4.2. Still open: A7–A15 during refresh, d_oe start on writes, read-data sampling edge.
