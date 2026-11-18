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
5. **Reset:** minimum low time is **3 clock cycles** (TM p.70, note C), and the first fetch cycle is still to be found (TM §8/§4 [check]), with the same "which cycles are compared" table as the 6502's §5.

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

**Refresh address = {I, R}** (TM §2.0 item 5, PDF p.10: R's data "is sent out on the lower portion of the address bus", and "during refresh, the contents of the I register are placed on the upper 8 bits of the address bus"). R's low 7 bits increment "after each instruction fetch", and bit 7 stays as last loaded by `LD R,A`. *Decision*: A7 carries R bit 7. TM §3.0 only guarantees the lower 7 bits as a refresh address, but the low byte is R, so A7 = R[7] is the natural reading. The increment is once per M1, so a prefixed opcode (CB/DD/ED/FD) increments R twice. That follows from M1 being "generated as each op code byte is fetched" (§2) [check against PM's R description].

### 4.2 Memory read and write, not M1 (Figure 4.0-2, p.13), 3 T states plus waits
| half | `a` | `mreq_n` | `rd_n` (read) | `wr_n` (write) | `d_oe` (write) |
|------|-----|----------|---------------|----------------|----------------|
| T1H | address | 1 | 1 | 1 | 0 |
| T1L | address | **0** | **0** | 1 | **1** (DATA OUT starts mid-T1: Figure 4.0-2, and tD(D) in the A.C. timing diagram, p.71, is measured from that falling edge) |
| T2H | address | 0 | 0 | 1 | 1 |
| T2L | address | 0 | 0 | **0** | 1 |
| T3H | address | 0 | 0 | 0 | 1 |
| T3L | address | **1** | **1** | **1** | 1 |
| next T1H | next address | | | | 0 |

- WAIT is sampled at the edge that starts T2L, and Tw states are inserted between T2 and T3, as in M1 (Figure 4.0-2A).
- **Read data is taken at the edge that starts T3L.** TM §11, p.70: tSΦ̄(D) is "Data Setup Time to **Falling** Edge of Clock During M2 to M5", while M1 uses tSΦ(D), the "Rising Edge of Clock During M1 Cycle" (§4.1). This confirms the figure, whose IN window ends at T3's falling edge.
- On writes, `d_oe` drops at the next T1H: tF(D), data float, is measured from that rising edge (p.71).
- `m1_n` = 1 and `rfsh_n` = 1 throughout.

### 4.3 I/O read and write (Figure 4.0-3, 4.0-3A, page image p.15), 4 T states plus waits
"During I/O operations a single wait state is automatically inserted" (TM p.14): T1, T2, **Tw\***, T3. WAIT is sampled during Tw\* (at the edge that starts Tw\*L), and further Tw follow while it's 0.

| half | `a` | `iorq_n` | `rd_n` (in) | `wr_n` (out) | `d_oe` (out) | `mreq_n` |
|------|-----|----------|-------------|--------------|--------------|----------|
| T1H | port address | 1 | 1 | 1 | 0 | 1 |
| T1L | port address | 1 | 1 | 1 | **1** | 1 |
| T2H | port address | **0** | **0** | **0** | 1 | 1 |
| T2L, Tw\*H, Tw\*L | port address | 0 | 0 | 0 | 1 | 1 |
| T3H | port address | 0 | 0 | 0 | 1 | 1 |
| T3L | port address | **1** | **1** | **1** | 1 | 1 |
| next T1H | | | | | 0 | |

- **IORQ, RD and WR fall at T2's *rising* edge**, not mid-T1 as for memory. Input data is taken at the edge that starts T3L (the IN window, and tSΦ̄(D) as for M2–M5).
- `a`: the figure labels only A0–A7 "PORT ADDRESS". What A8–A15 carry depends on the instruction (TM §5) [check], and it will be specified per instruction in §6.
- `m1_n` = 1 throughout ("I/O operations never occur during M1 time", §2).

### 4.4 Bus request / acknowledge (Figure 4.0-4, page image p.16)
- `busrq_n` is sampled "with the rising edge of the last clock period of any machine cycle" (TM p.14). If it's 0, then from "the rising edge of the next clock pulse" the CPU floats `a`, the data bus, `mreq_n`, `rd_n`, `wr_n`, `iorq_n` and **`rfsh_n`** (all five are listed as floating in the figure), and drives `busak_n` = 0. The CPU spends Tx states in this state.
- `busrq_n` is sampled again at the rising edge of each Tx. Once it's sampled 1, `busak_n` returns to 1 **at the falling edge** in that Tx (TM p.70: tDH(BA) "BUSAK Delay From Falling Edge of Clock, BUSAK High"; it falls at a rising edge, tDL(BA)). The CPU drives the buses again from the next rising edge, which starts T1 of the next machine cycle.
- **Not floated:** `m1_n` and `halt_n` (not in the figure's list) [check against TM §3].
- "During a bus request cycle, the CPU cannot be interrupted by either a NMI or an INT signal" (p.14).
- *Modelling (proposed):* a floating output is represented by a 1-bit output enable per group: `bus_oe` for `a`, `mreq_n`, `iorq_n`, `rd_n`, `wr_n` and `rfsh_n`; `d_oe` for data. When an output enable is 0, the pin's value is not compared. The same will apply during reset (§2).

### 4.5 Interrupt acknowledge, mode-independent part (Figure 4.0-5, page image p.16)
`int_n` is sampled "with the rising edge of the last clock at the end of any instruction" and ignored if the IFF is reset or `busrq_n` is 0 (TM p.16). It's accepted with a **special M1**: T1, T2, **Tw\***, **Tw\***, T3, T4.

| half | `a` | `m1_n` | `mreq_n` | `iorq_n` | `rd_n` | `rfsh_n` |
|------|-----|--------|----------|----------|--------|----------|
| T1H | PC | **0** | 1 | 1 | 1 | 1 |
| T1L, T2H, T2L, Tw\*1H | PC | 0 | 1 | 1 | 1 | 1 |
| Tw\*1L | PC | 0 | 1 | **0** | 1 | 1 |
| Tw\*2H, Tw\*2L | PC | 0 | 1 | 0 | 1 | 1 |
| T3H | {I, R} | **1** | 1 | **1** | 1 | **0** |
| T3L, T4H | {I, R} | 1 | **0** | 1 | 1 | 0 |
| T4L | {I, R} | 1 | **1** | 1 | 1 | 0 |

- **No MREQ and no RD** before T3. The vector is taken from `d_in` at the edge that starts T3H (the IN window in the figure, as M1's opcode). WAIT is sampled at the edge that starts Tw\*2L, and user wait states go after the two Tw\* (Figure 4.0-5B, p.17).
- What follows the vector (mode 0, 1 or 2) is §8.

### 4.6 NMI response (Figure 4.0-6, page image p.18)
- `nmi_n` is "sampled at the same time as the interrupt line", has priority over INT, and can't be disabled (TM p.18). Being edge-triggered (§2), what's sampled is a latched falling edge [check TM §8 for where the edge is latched].
- The first cycle after acceptance is an **M1 like an opcode fetch**: the same `m1_n`, `mreq_n`, `rd_n` and `rfsh_n` as §4.1, with `a` = PC, but **the data read is ignored** ("similar to a normal memory read … the content of the data bus is ignored"). Then the PC is pushed (two memory writes, §4.2), and execution continues at **0066H**. The exact machine cycles and T counts are §8 [check TM §8.0].

### 4.7 HALT and HALT exit (Figure 4.0-7, page image p.18)
- After HALT, "each cycle in the halt state is a normal M1 (fetch) cycle except that the data received from the memory is ignored and a NOP instruction is forced internally". So a halted CPU shows the §4.1 sequence every 4 T states, with refresh (TM p.18). The address is [check TM §5/§8: the PC stays at the HALT's successor, or keeps incrementing].
- `halt_n` falls at the edge that starts **T4L** of the HALT instruction's M1, and rises at the edge that starts T4L of the halted M1 in which the interrupt was accepted. Both are falling edges: TM p.70 tD(HT), "HALT Delay Time From Falling Edge of Clock", and Figure 4.0-7.
- `int_n` and `nmi_n` are "sampled with the rising clock edge during each T4 state". If NMI, or INT with IFF set, is accepted, the next cycle is the matching interrupt acknowledge (§4.5 or §4.6). **NMI wins if both are present.**

## 8. Interrupts (TM §8.0, pp.55–57, text layer; normative once checked)

### 8.1 IFF1 and IFF2 (TM p.55, Figure 8.0-1)
IFF1 "actually disables interrupts from being accepted"; IFF2 is "temporary storage location for IFF1".

| Action | IFF1 | IFF2 | also |
|--------|------|------|------|
| Reset | 0 | 0 | |
| DI | 0 | 0 | |
| EI | 1 | 1 | INT is **not** accepted until after the instruction **following** EI ("This single instruction delay is necessary for cases when the following instruction is a return") |
| LD A,I / LD A,R | – | – | P/V ← IFF2 |
| Accept NMI | **0** | – | IFF2 keeps the old IFF1 |
| Accept INT (any mode) | 0 | 0 | "both IFF1 and IFF2 are automatically reset" |
| RETN | ← IFF2 | – | |

### 8.2 Responses
- **NMI** (TM p.56): accepted "at all times" (but not during a bus request, §4.4). "The CPU ignores the next instruction that it fetches and instead does a restart to location 0066H. Thus, it behaves exactly as if it had received a restart instruction." So the sequence is the §4.6 M1, with data ignored, then the two pushes of PC (§4.2 writes), then PC = 0066H. The T-state count is from the RST timing in PM [check].
- **INT, mode 0** (8080 mode, the mode after reset): the device puts an instruction on the bus in the §4.5 acknowledge cycle, and the CPU executes it. "The number of clock cycles … is 2 more than the normal number for the instruction" (the two Tw\*). *Proposed*: tests use only **RST p** (one byte) in mode 0, as the 8080 spec did. Multi-byte instructions in mode 0 are not specified.
- **INT, mode 1**: a restart to **0038H**, with the data bus ignored, "2 more than normal" cycles.
- **INT, mode 2**: pointer = {I, vector}. The CPU pushes PC and loads PC from the two bytes at the pointer, low byte first. "Only 7 bits are required from the interrupting device as the least significant bit must be a zero." *Proposed*: tests always supply bit 0 = 0, and bit 0 = 1 is not specified. TM gives **19 clock periods** (7 to fetch the vector, 6 to push PC, 6 to read the table). That's one T more than §4.5's 6-T acknowledge cycle shows, so the per-cycle breakdown is [check] against PM.

### 8.3 Still open
- Where the NMI falling edge is latched, and how long `nmi_n` must stay low in the model (TM gives tw(NMI) ≥ 80 ns, p.70). *Proposed*, as for the 6502: an edge detector runs on every model edge, and tests hold `nmi_n` low ≥ 2 T states and change it only at a T1H edge.
- Priority NMI > INT at the same sampling edge (TM p.18, HALT exit; assumed to hold everywhere) [check PM].
- `int_n` is level-sensitive; the device holds it until acknowledged (TM §3: "honored at the end of the current instruction").

## 5–7. Reset, instructions, tests
To be written from TM §5–8 and PM, in the 6502 spec's layout: the flags per instruction, the interrupt modes, and the behaviour list C1–C8.

## 9. Acceptance test candidates (licences to check before use)
1. **zexdoc** (Frank D. Cringle's Z80 instruction exerciser, documented flags only), the Z80 counterpart of 8080EXM. It's fetched at test time and never committed. Licence to read from its header (GPL, as remembered; **not yet checked**).
2. **zexall**: the same, including the undocumented X/Y flags. Only if §1's flag decision changes.
3. **Per-instruction vectors with bus activity**: SingleStepTests `z80` set, a cross-check only, as for the 6502.
4. **Examples from the Zilog manuals** (TM §10, the PM).

## 10. Datasheet check
Every [check] gets a line here with the page it was confirmed on.
- [x] Pin list and functions (TM §3.0, pp.7–9, from the text layer; the page image is still to be compared for OCR errors): table in §2.
- [x] M1 and memory read/write timing (TM §4.0, Figures 4.0-1, 4.0-1A, 4.0-2, page images pp.12–13): §4.1, §4.2.
- [x] Sampling edges (TM §11 A.C. characteristics p.70 and timing diagram p.71, page image): M1 data at the rising edge, M2–M5 data at the falling edge, WAIT at the falling edge, INT, BUSRQ and RESET set up to the rising edge; write data from T1's falling edge, floating at the next rising edge. Note C: "The RESET signal must be active for a minimum of 3 clock cycles" (for §5).
- [x] Refresh address {I, R} (TM §2.0 item 5, PDF p.10, text layer).
- [x] I/O cycles, bus request/acknowledge, interrupt acknowledge (TM §4.0, Figures 4.0-3, 4.0-3A, 4.0-4, 4.0-5, 4.0-5B, page images pp.15–17; text p.14, 16): §4.3–4.5.
- [x] NMI response and HALT exit (TM §4.0, Figures 4.0-6, 4.0-7, page image p.18), with edges from TM p.70 (tD(HT), tDH(BA)): §4.6, §4.7. **TM §4.0 is now fully read.**
- [x] Interrupt enable flip-flops, NMI response, INT modes 0/1/2 (TM §8.0, pp.55–57, text layer): §8.
