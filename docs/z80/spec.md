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
5. **Reset:** *proposed in §5* (≥ 3 T states; the first M1 at the first rising edge with `reset_n` = 1; registers other than PC, I, R, IFF and IM not reset). The TM gives no post-reset timing (searched 2026-11-18).

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
- **NMI** (TM p.56): accepted "at all times" (but not during a bus request, §4.4). "The CPU ignores the next instruction that it fetches and instead does a restart to location 0066H." Per MK3880 §12 (p.83): **11 T states**, "the first M1 being a dummy OP Code Fetch of 5 T-States long. The Program Counter is not advanced, the OP Code on the data bus is ignored and an internal Restart is done to address 66H. The following two Machine Cycles are a write of the Program Counter to the Stack" (so 5 + 3 + 3).
- **INT, mode 0** (8080 mode, the mode after reset): the device puts an instruction on the bus in the §4.5 acknowledge cycle, and the CPU executes it. "The number of clock cycles … is 2 more than the normal number for the instruction" (the two Tw\*). *Proposed*: tests use only **RST p** (one byte) in mode 0, as the 8080 spec did. Multi-byte instructions in mode 0 are not specified.
- **INT, mode 1**: a restart to **0038H**, with the data bus ignored, "2 more than normal" cycles.
- **INT, mode 2**: pointer = {I, vector}. The CPU pushes PC and loads PC from the two bytes at the pointer, low byte first. "Only 7 bits are required from the interrupting device as the least significant bit must be a zero." *Proposed*: tests always supply bit 0 = 0, and bit 0 = 1 is not specified. TM gives **19 clock periods** (7 to fetch the vector, 6 to push PC, 6 to read the table). MK3880 §12 (p.84): "During the INTA cycle (M1) a Vector is sent in … M2 and M3 are used to Stack the Program Counter … During M4 and M5 the Service Routines address is read from this table". So INTA is 7 T, one more than §4.5's figure shows; where that T falls is [check] against MK3880's table (page image).

### 8.3 Still open
- Where the NMI falling edge is latched, and how long `nmi_n` must stay low in the model (TM gives tw(NMI) ≥ 80 ns, p.70). *Proposed*, as for the 6502: an edge detector runs on every model edge, and tests hold `nmi_n` low ≥ 2 T states and change it only at a T1H edge.
- Priority NMI > INT at the same sampling edge (TM p.18, HALT exit; assumed to hold everywhere) [check PM].
- `int_n` is level-sensitive; the device holds it until acknowledged (TM §3: "honored at the end of the current instruction").

## 6. Instructions

### 6.0 Which opcodes are documented
**Source:** PM Appendix C, "Instruction Set Numerical Order" (PDF pp.302–305, page images): Zilog's own Z-80 cross-assembler listing (version 1.06 of 06/18/76, run 07/09/76) of every instruction form in numeric order. It has **694 statements**, numbered 1–694, the last being `SET 7,(IY+IND)` (FD CB d FE).

| Group | Statements | Forms | Our structural count |
|-------|-----------|-------|----------------------|
| unprefixed | 1–500, with CB | 252 | 256 minus the 4 prefixes CB, DD, ED, FD |
| CB | (in 1–500) | 248 | 256 minus CB 30–37 (the undocumented "SLL") |
| DD (IX) | 501–570 | 70 | 39 + 31 DD CB d forms |
| ED | 571–624 | **54** | **58** |
| FD (IY) | 625–694 | 70 | as DD |

**The ED group is 4 short of a structural count, and the reason matters.** Read from the page image of PDF p.304: statement 583 is `ED4D RETI`, then 584 `ED50 IN D,(C)`; and 594 `ED5E IM 2`, then 595 `ED60 IN H,(C)`. So the listing **omits**:
- `ED 4F` **LD R,A** and `ED 5F` **LD A,R**. Both *are* documented elsewhere: TM §2.0 item 5 ("as the result of an LD R,A instruction") and TM §8.0 ("When a … (LD A,R) instruction is executed, the state of IFF2 is copied into the parity flag"). The listing is an assembler test, not an exhaustive list.
- `ED 63` and `ED 6B`, the ED encodings of LD (nn),HL / LD HL,(nn) (the one-byte forms `22`/`2A` are listed). These *are* documented by PM's generic descriptions: `LD dd,(nn)` = ED 01dd1011 (PM p.57) and `LD (nn),dd` = ED 01dd0011 (PM p.62), each saying "Register pair dd defines BC, DE, HL, or SP", with HL = 10, 6 M cycles, "20 (4,4,3,3,3,3)" T states. So ED 6B = LD HL,(nn) and ED 63 = LD (nn),HL in 20 T states, alongside the 16-T one-byte forms.

***Decision* (proposed):** the documented set is Appendix C's **694 forms plus the 4 the listing omits (`LD R,A`, `LD A,R`, `ED 63`, `ED 6B`) = 698**. That's exactly our structural count (252 + 248 + 58 + 70 + 70), so every row of the table above now agrees. Everything else is undocumented: not specified, and not executed by tests (§1). As for the 6502, the final opcode table (§6.1) will be cross-checked by script against this list.

### 6.2 Flags (TM §6.0, pp.39–41; Table 6.0-1 read from the page image, p.41)
F = `S Z X H X P/V N C` (bit 7 → bit 0); "X means flag is indeterminate" (p.39). **Bits 5 and 3 are never compared** (§1).

Table 6.0-1, transcribed. `↕` means set by the result, `•` unchanged, `0`/`1` forced, `X` "don't care", `V` overflow, `P` parity. "Any instruction not appearing in this table does not affect any of the flags" (p.40).

| Instruction | C | Z | P/V | S | N | H |
|---|---|---|---|---|---|---|
| ADD A,s; ADC A,s | ↕ | ↕ | V | ↕ | 0 | ↕ |
| SUB s; SBC A,s; CP s; NEG | ↕ | ↕ | V | ↕ | 1 | ↕ |
| AND s | 0 | ↕ | P | ↕ | 0 | 1 |
| OR s; XOR s | 0 | ↕ | P | ↕ | 0 | 0 |
| INC s | • | ↕ | V | ↕ | 0 | ↕ |
| DEC m | • | ↕ | V | ↕ | 1 | ↕ |
| ADD DD,ss (16-bit) | ↕ | • | • | • | 0 | **X** |
| ADC HL,ss | ↕ | ↕ | V | ↕ | 0 | **X** |
| SBC HL,ss | ↕ | ↕ | V | ↕ | 1 | **X** |
| RLA; RLCA; RRA; RRCA | ↕ | • | • | • | 0 | 0 |
| RL m; RLC m; RR m; RRC m; SLA m; SRA m; SRL m | ↕ | ↕ | P | ↕ | 0 | 0 |
| RLD; RRD | • | ↕ | P | ↕ | 0 | 0 |
| DAA | ↕ | ↕ | P | ↕ | • | ↕ |
| CPL | • | • | • | • | 1 | 1 |
| SCF | 1 | • | • | • | 0 | 0 |
| CCF | ↕ | • | • | • | 0 | **X** |
| IN r,(C) | • | ↕ | P | ↕ | 0 | 0 |
| INI; IND; OUTI; OUTD | • | ↕ (Z = 0 if B ≠ 0, else 1) | **X** | **X** | 1 | **X** |
| INIR; INDR; OTIR; OTDR | • | 1 | **X** | **X** | 1 | **X** |
| LDI; LDD | • | **X** | ↕ (1 if BC ≠ 0) | **X** | 0 | 0 |
| LDIR; LDDR | • | **X** | 0 | **X** | 0 | 0 |
| CPI; CPIR; CPD; CPDR | • | ↕ (1 if A = (HL)) | ↕ (1 if BC ≠ 0) | ↕ | 1 | **X** |
| LD A,I; LD A,R | • | ↕ | IFF (IFF2, §8.1) | ↕ | 0 | 0 |
| BIT b,s | • | ↕ (bit b → Z) | **X** | **X** | 0 | 1 |

**Open decision 6: the "X" flags that the acceptance test checks.** zexdoc's flag masks follow "Documented flags … as per **Mostek** Z80 Technical Manual" (its source comment, line 49). They agree with Table 6.0-1 for the 16-bit adds (mask C7, H excluded) and BIT (mask 53, S and P/V excluded). But with mask D7 it **does check**, where Zilog 1977 says X:
- **S and Z after LDI/LDD/LDIR/LDDR** (tests `ldi1`, `ldi2`, `ldd1`, `ldd2`);
- **H after CPI/CPD** (`cpi1`, `cpd1`);
- **H after CCF** (in the `daa` test).

Block I/O isn't exercised by zexdoc. This is the same situation as the 6502's decimal flags (turichips#32). The options:
- (a) specify those flags from **Mostek's Z80 manuals** (the second-source manufacturer; e.g. *MK78515 Mostek Z80 Programming Manual* V2.0, Oct 1978, on bitsavers), which zexdoc's author names as its reference [to read];
- (b) leave them unspecified and drop zexdoc, since its masks can't be changed without new reference CRCs from real hardware;
- (c) leave them unspecified, keep zexdoc, and accept that the RTL must happen to match it.

**Mostek read (2026-11-18), for option (a):** *MK78515 Mostek Z80 Programming Manual* V2.0, October 1978 (bitsavers `components/mostek/Z80/`, 312 pages, text layer). It gives definite values for every flag in question, all of them what zexdoc expects:

| Instruction | Mostek | Zilog 1977 |
|---|---|---|
| CCF | "H: Previous carry will be copied" (p.2-55) | X |
| LDI; LDD; LDIR; LDDR | "S: Not affected", "Z: Not affected" (pp.2-169, 2-165, 2-171, 2-167) | X |
| CPI; CPD; CPIR; CPDR | "H: Set if there is a borrow from bit 4" (pp.2-62, 2-58, 2-64, 2-60) | X |

All four block compares read (CPD p.2-58: 16 T states, 4,4,3,5). Mostek and Zilog agree on every flag Zilog does define, as far as checked.

**Recommendation: (a).** Where Zilog's 1977 table says X and Mostek's 1978 manual gives a value, that value is normative, cited to Mostek. Zilog's own X flags that Mostek also leaves open, and the block-I/O S, H and P/V, stay not compared. Mostek was Zilog's licensed second source, so this is a manufacturer's document, not an emulator. It needs Sai's call with the rest of the spec.

### 6.1 Per-instruction timing (in progress)
The source per instruction is PM's "M CYCLES … T STATES n(t1,t2,…)" line, which gives each M cycle's length. TM §7 (p.43) gives only totals. Groups as in PM's contents (p.25): 8-bit load, 16-bit load, exchange/block transfer/search, 8-bit arithmetic and logic, general-purpose arithmetic and CPU control, 16-bit arithmetic, rotate and shift, bit set/reset/test, jump, call and return, input and output.

**8-bit load group.** Lengths from PM pp.26–51 (text layer). Cycle types from **MK3880 §12, p.85** (page image). Legend (MK3880 p.85):
- OCF: opcode fetch (§4.1)
- OD / ODL / ODH: operand data read (low / high byte)
- MR / MW: memory read / write (§4.2)
- IO: internal operation, no bus cycle
- (n): T states

| Instruction | Bytes | M cycles | T states | Cycle types (MK3880 p.85) |
|---|---|---|---|---|
| LD r,r' | 1 | 1 | 4 | OCF(4) |
| LD r,n | 2 | 2 | 7 | OCF(4) OD(3) |
| LD r,(HL) | 1 | 2 | 7 | OCF(4) MR(3) |
| LD (HL),r | 1 | 2 | 7 | OCF(4) MW(3) |
| LD r,(IX+d); LD r,(IY+d) | 3 | 5 | 19 | OCF(4) OCF(4) OD(3) IO(5) MR(3) |
| LD (IX+d),r; LD (IY+d),r | 3 | 5 | 19 | OCF(4) OCF(4) OD(3) IO(5) MW(3) |
| LD (HL),n | 2 | 3 | 10 | OCF(4) OD(3) MW(3) |
| LD (IX+d),n; LD (IY+d),n | 4 | 5 | 19 | **not in MK3880's table.** *Derived (decision 7(b))*: OCF(4) OCF(4) OD(3) OD(5) MW(3), i.e. d read, then n read in a 5-T cycle (3-T read + 2 internal T), then the write. To confirm against another MK3880 page or a later source [check] |
| LD A,(BC); LD A,(DE) | 1 | 2 | 7 | OCF(4) MR(3) |
| LD (BC),A; LD (DE),A | 1 | 2 | 7 | OCF(4) MW(3) |
| LD A,(nn) | 3 | 4 | 13 | OCF(4) ODL(3) ODH(3) MR(3) |
| LD (nn),A | 3 | 4 | 13 | OCF(4) ODL(3) ODH(3) MW(3) |
| LD A,I; LD A,R; LD I,A; LD R,A | 2 | 2 | 9 | OCF(4) **OCF(5)** |

**16-bit load group.** Lengths from PM pp.52–75 (text layer). Cycle types from MK3880 p.85 (page image). SWH/SWL are stack writes of the high/low byte; SRL/SRH stack reads.

| Instruction | Bytes | M cycles | T states | Cycle types |
|---|---|---|---|---|
| LD dd,nn | 3 | 3 | 10 | OCF(4) ODL(3) ODH(3) |
| LD IX,nn; LD IY,nn | 4 | 4 | 14 | OCF(4) OCF(4) ODL(3) ODH(3) |
| LD HL,(nn) | 3 | 5 | 16 | OCF(4) ODL(3) ODH(3) MRL(3) MRH(3) |
| LD (nn),HL | 3 | 5 | 16 | OCF(4) ODL(3) ODH(3) MWL(3) MWH(3) |
| LD dd,(nn) (ED 4B/5B/6B/7B) | 4 | 6 | 20 | OCF(4) OCF(4) ODL(3) ODH(3) MRL(3) MRH(3) |
| LD (nn),dd (ED 43/53/63/73) | 4 | 6 | 20 | OCF(4) OCF(4) ODL(3) ODH(3) MWL(3) MWH(3) |
| LD IX,(nn); LD IY,(nn) | 4 | 6 | 20 | OCF(4) OCF(4) ODL(3) ODH(3) MRL(3) MRH(3) |
| LD (nn),IX; LD (nn),IY | 4 | 6 | 20 | OCF(4) OCF(4) ODL(3) ODH(3) MWL(3) MWH(3) |
| LD SP,HL | 1 | 1 | 6 | **OCF(6)** |
| LD SP,IX; LD SP,IY | 2 | 2 | 10 | OCF(4) **OCF(6)** |
| PUSH qq | 1 | 3 | 11 | **OCF(5)** (SP − 1 in the extra T) SWH(3) at SP−1, then SWL(3) at SP−2 |
| PUSH IX; PUSH IY | 2 | 4 | 15 | OCF(4) **OCF(5)** SWH(3) SWL(3) |
| POP qq | 1 | 3 | 10 | OCF(4) **SRL(3)** at SP, then **SRH(3)** at SP+1 (see note) |
| POP IX; POP IY | 2 | 4 | 14 | OCF(4) OCF(4) SRL(3) SRH(3) |

Notes:
- **POP order.** MK3880 p.85 labels POP's cycles "SRH(3) SRL(3)", the same order as its PUSH row. But PM p.72 (Zilog) says POP "first loads into the low order portion of qq, the byte at the memory location corresponding to the contents of SP; then SP is incremented and … the high order portion". **Zilog's text governs**: M2 reads (SP) into the low byte and M3 reads (SP+1) into the high byte. That's also the only order consistent with PUSH's layout.
- MK3880's own RET row (p.88) reads "SRL(3) SRH(3)", low byte first, which confirms the POP ruling above.
- **PUSH IX.** PM's PUSH IX page prints "M CYCLES: 3" next to "15(4,5,3,3)", four lengths; PUSH IY's page prints 4. We take 4 [check page image].

**Exchange, block transfer and search group.** Lengths from PM pp.76–98 (text layer). Cycle types from MK3880 pp.85–86 (page images).

| Instruction | Bytes | M cycles | T states | Cycle types |
|---|---|---|---|---|
| EX DE,HL; EX AF,AF'; EXX | 1 | 1 | 4 | OCF(4) |
| EX (SP),HL | 1 | 5 | 19 | OCF(4) SRL(3) at SP, SRH(4) at SP+1, SWH(3) at SP+1, SWL(5) at SP |
| EX (SP),IX; EX (SP),IY | 2 | 6 | 23 | OCF(4) OCF(4) SRL(3) **SRH(4)** SWH(3) SWL(5) (see note) |
| LDI; LDD | 2 | 4 | 16 | OCF(4) OCF(4) MR(3) at HL, MW(5) at DE |
| CPI; CPD | 2 | 4 | 16 | OCF(4) OCF(4) MR(3) at HL, **IO(5)** (see note) |
| LDIR; LDDR | 2 | 5 / 4 | 21 if BC ≠ 0 after the step, 16 if BC = 0 | as LDI/LDD, plus IO(5) "only if BC ≠ 0" (PC − 2, so the instruction is refetched) |
| CPIR; CPDR | 2 | 5 / 4 | 21 if repeating, 16 if not | as CPI/CPD, plus IO(5) when repeating. PM p.91: "If decrementing causes the BC to go to zero or if A=(HL), the instruction is terminated". So it **repeats while BC ≠ 0 and A ≠ (HL)**, with 21 T "For BC≠0 and A≠(HL)". The page's next sentence prints "A=(HL)" where it means A≠(HL). "Interrupts will be recognized and two refresh cycles will be executed after each data transfer". BC = 0 at the start loops through 64K |

Notes:
- **EX (SP),IX/IY.** MK3880 p.86's row shows SRH(3), which sums to 22 T. PM gives 23 (4,4,3,4,3,5), the same pattern as EX (SP),HL's SRH(4) on the row above, so **SRH(4)**. PM governs the lengths.
- **CPI/CPD/CPIR/CPDR.** MK3880 p.86 lists them in one row with LDI/LDD as "MR(3) MW(5)". A compare writes nothing: PM's operation for CPI is "A − (HL), HL ← HL+1, BC ← BC−1". So their 5-T third cycle is taken as **IO(5)**, with no write strobe, our reading of the shared row [check].
- Addresses on each access: EX (SP),HL reads (SP) and (SP+1) and writes them back high first. That's per MK3880's arrows (SP+1 after SRL, SP−1 after SWH).

**8-bit arithmetic and logic group.** Lengths from PM pp.99–130 (text layer, including its per-page tables). Cycle types from MK3880 p.86 (page image). `alu` is any of ADD A, ADC A, SUB, SBC A, AND, OR, XOR, CP; their timings are identical.

| Instruction | Bytes | M cycles | T states | Cycle types |
|---|---|---|---|---|
| alu r | 1 | 1 | 4 | OCF(4) |
| alu n | 2 | 2 | 7 (4,3) | OCF(4) OD(3) |
| alu (HL) | 1 | 2 | 7 (4,3) | OCF(4) MR(3) |
| alu (IX+d); alu (IY+d) | 3 | 5 | 19 (4,4,3,5,3) | OCF(4) OCF(4) OD(3) IO(5) MR(3) |
| INC r; DEC r | 1 | 1 | 4 | OCF(4) |
| INC (HL); DEC (HL) | 1 | 3 | 11 (4,4,3) | OCF(4) **MR(4)** MW(3) |
| INC (IX+d); DEC (IX+d); same for IY | 3 | 6 | 23 (4,4,3,5,4,3) | OCF(4) OCF(4) OD(3) IO(5) **MR(4)** MW(3) |

The read-modify-write `MR(4)` is a 3-T read plus 1 internal T (the increment), and it's followed by the write. The extra T's position follows the lengthened-cycle rule below.

**General-purpose arithmetic and CPU control group.** Lengths from PM pp.131–145 (text layer). Cycle types from MK3880 p.86 (page image).

| Instruction | Bytes | M cycles | T states | Cycle types |
|---|---|---|---|---|
| DAA; CPL; CCF; SCF; NOP; HALT; DI; EI | 1 | 1 | 4 | OCF(4) |
| NEG; IM 0; IM 1; IM 2 | 2 | 2 | 8 (4,4) | OCF(4) OCF(4) |

HALT's following cycles are the halted M1s of §4.7. The EI delay is §8.1.

**16-bit arithmetic group.** Lengths from PM pp.146–162 (text layer). Cycle types from MK3880 p.87 (page image).

| Instruction | Bytes | M cycles | T states | Cycle types |
|---|---|---|---|---|
| ADD HL,ss | 1 | 3 | 11 (4,4,3) | OCF(4) IO(4) IO(3) |
| ADC HL,ss; SBC HL,ss | 2 | 4 | 15 (4,4,4,3) | OCF(4) OCF(4) IO(4) IO(3) |
| ADD IX,pp; ADD IY,rr | 2 | 4 | 15 (4,4,4,3) | OCF(4) OCF(4) IO(4) IO(3) |
| INC ss; DEC ss | 1 | 1 | 6 | **OCF(6)** |
| INC IX; DEC IX; INC IY; DEC IY | 2 | 2 | 10 (4,6) | OCF(4) **OCF(6)** |

IO cycles have no bus activity. So in ADD HL,ss the 7 T after the fetch are bus-idle, under the lengthened-cycle rule below.

**Rotate and shift group.** Lengths from PM pp.163–201 (text layer). Cycle types from MK3880 p.87 (page image). `rot` is any of RLC, RL, RRC, RR, SLA, SRA, SRL; their timings are identical (PM per-page tables).

| Instruction | Bytes | M cycles | T states | Cycle types |
|---|---|---|---|---|
| RLCA; RLA; RRCA; RRA | 1 | 1 | 4 | OCF(4) |
| rot r | 2 | 2 | 8 (4,4) | OCF(4) OCF(4) |
| rot (HL) | 2 | 4 | 15 (4,4,4,3) | OCF(4) OCF(4) MR(4) MW(3) |
| rot (IX+d); rot (IY+d) | 4 | 6 | 23 (4,4,3,5,4,3) | OCF(4) OCF(4) OD(3) **OD(5)** MR(4) MW(3) (see note) |
| RLD; RRD | 2 | 5 | 18 (4,4,3,4,3) | OCF(4) OCF(4) MR(3) IO(4) MW(3) |

**Bit set, reset and test group.** Lengths from PM pp.202–218 (text layer). Cycle types from MK3880 pp.87–88 (page images).

| Instruction | Bytes | M cycles | T states | Cycle types |
|---|---|---|---|---|
| BIT b,r; SET b,r; RES b,r | 2 | 2 | 8 (4,4) | OCF(4) OCF(4) |
| BIT b,(HL) | 2 | 3 | 12 (4,4,4) | OCF(4) OCF(4) MR(4) |
| SET b,(HL); RES b,(HL) | 2 | 4 | 15 (4,4,4,3) | OCF(4) OCF(4) MR(4) MW(3) |
| BIT b,(IX+d); BIT b,(IY+d) | 4 | 5 | 20 (4,4,3,5,4) | OCF(4) OCF(4) OD(3) **OD(5)** MR(4) |
| SET/RES b,(IX+d); same for IY | 4 | 6 | 23 (4,4,3,5,4,3) | OCF(4) OCF(4) OD(3) **OD(5)** MR(4) MW(3) |

**Note: the DD CB d op / FD CB d op forms.** These are 4 bytes. MK3880 shows OCF(4)/OCF(4) for DD and CB, OD(3) for d, then **IO(5)**, then the data cycles. That accounts for only 3 bytes on the bus, but the 4th byte (the operation) is in memory and has to be read. The only cycle that can contain it is the 5-T M3. *Decision (proposed)*: M3 is **OD(5)**, a 3-T operand read of the operation byte at PC (`m1_n` = 1 and no refresh, because Zilog's M1 description lists only CB, DD, ED, FD as M1-fetched prefixes), followed by 2 internal T. MK3880's "IO(5)" label is taken as a simplification [check against a later Zilog source if one is found].

Lengthened cycles (an OCF of 5 or 6 T, an IO of 5 T, an OD of 5 T): **where the extra T states sit, and what the pins show during them**, is a §4 rule still to write. *Proposed*: the extra T states follow the cycle's normal last T state (T4 of an OCF, T3 of a read). During them `mreq_n`, `iorq_n`, `rd_n` and `wr_n` are inactive, `m1_n` = 1, `rfsh_n` = 1, and `a` is not compared [check against MK3880 §4 figures]. An IO cycle has no bus activity at all.

**Open decision 7: what each M cycle does on the bus.** C2 compares pins in every half T state (§4.0), so for each M cycle we need its *type*: opcode fetch (§4.1), memory read or write (§4.2), I/O (§4.3), or internal (no bus cycle). We also need, for M cycles longer than the basic 3 T, *where* the extra T states fall. The PM gives only the lengths, and the same lengths mean different things:
- `LD r,(IX+d)` (4,4,3,5,3): M3 reads d, then **M4 (5 T) can only be internal** (the add; no byte is left to transfer), then M5 reads (IX+d).
- `LD (IX+d),n` (4,4,3,5,3): M3 reads d, then **M4 (5 T) must read n** plus 2 internal T, then M5 writes.

Neither TM (1977), PM (1978), Mostek MK78515 (1978) nor Zilog's 1987 Technical Manual (searched 2026-11-18) gives a per-M-cycle breakdown. Options:
- (a) Find a manufacturer's per-cycle table (a later Zilog document, e.g. the Z80 CPU User Manual), and cite it, as for Mostek in decision 6.
- (b) Specify each instruction's cycle types ourselves as *Decisions*, from the lengths and what the instruction must transfer. Where that leaves a choice (where in a 5-T read the 2 internal T states go), the strobes are fixed by our rule and `a` isn't compared during internal T states.
- (c) Compare pins only within bus cycles (`mreq_n`/`iorq_n` active), and check the instruction's total T states, but not the placement of internal T states.

**Update (2026-11-18): option (a) has a source.** *MK3880 (Z80) Technical Manual*, Mostek, "Printed in USA December 1977". The copy found is as distributed by Cromemco (PDF title "Cromemco Z-80 Technical Manual 023-0045 197712", 91 pages, text layer; read locally, not committed). **§12 "Z80 Instruction Breakdown by Machine Cycle"** (p.83 on) "tabulates each Z80 instruction type and breaks each instruction down into its machine cycles and corresponding T States … This chart will allow the system designer to predict what the Z80 will do on each clock cycle." Its legend has typed cycles: OCF, OD, ODL/ODH, MR, MRL/MRH, MW, MWL/MWH, SRL/SRH, SWL/SWH, PR, PW, IO (internal operation), INTA. Its own worked examples match the PM lengths:
- `LD r,(IX+d)`: "two M1 cycles … followed by an Operand Data Read of the displacement d. Next … a five T-State Internal Operation which is the calculation of the Indexed address (IX+d). The last machine cycle … a Memory Read."
- `PUSH qq`: "Machine cycle 1 is extended by one cycle and the Stack Pointer is decremented in the extra T-State", then two writes, high byte first.
- `LDI`: OCF, OCF, MR, MW (5 T); `LDIR` adds a 5-T M cycle that decrements PC by 2 and refetches.

**Recommendation now: (a), with the cycle types taken from MK3880 §12 and cited per instruction.** That's Mostek again, Zilog's licensed second source, as in decision 6. §6.1 will gain a cycle-type column from its tables, read from the page images. Where an internal T state falls inside a longer M cycle and MK3880 doesn't say, it's (b) for that detail.

## 5. Reset

**What Zilog documents:**
- `reset_n` "forces the program counter to zero" and sets IFF (both IFF1 and IFF2, TM p.55) = 0, **I = 00H**, **R = 00H**, **interrupt mode 0** (TM §3.0 p.9).
- "During reset time, the address bus and data bus go to a high impedance state and all control output signals go to the inactive state" (p.9).
- "The RESET signal must be active for a minimum of 3 clock cycles" (TM p.70, note C), and it's set up to the **rising** edge of Φ (tS(RS), p.70).

**Not documented, so these are *Decisions* (proposed):**
1. **Other registers are not reset:** A, F, B, C, D, E, H, L, the alternate set A'…L', IX, IY and SP. As for the 6502 and 8080, the C8 preamble writes every one of them before anything reads it. Comparison has **no exemption window**.
2. **While `reset_n` = 0:** `bus_oe` = 0 and `d_oe` = 0 (floating, §4.4), so `a`, `mreq_n`, `iorq_n`, `rd_n`, `wr_n`, `rfsh_n` and the data bus are not compared. `m1_n` = 1, `halt_n` = 1 and `busak_n` = 1 ("inactive") are compared from the second T state of reset on.
3. **The first M1:** T1H of the first opcode fetch starts at **the first rising edge of Φ at which `reset_n` is sampled 1**, at address 0000H. The manuals give no delay here, so this is our choice. It's exact, so the RTL and the model can't disagree.
4. **Stimulus:** tests hold `reset_n` = 0 for **≥ 3 T states** (6 model cycles) and change it only at a rising edge (T-state boundary). `busrq_n`, `int_n` and `nmi_n` are held inactive from reset until the first M1 has started.

## 7. Tests
To be written from TM §5–8 and PM, in the 6502 spec's layout: the flags per instruction, the interrupt modes, and the behaviour list C1–C8.

## 9. Acceptance test candidates (licences to check before use)
1. **zexdoc** (Frank D. Cringle's Z80 instruction exerciser, documented flags only), the Z80 counterpart of 8080EXM.
   - **Licence checked** (2026-11-18, source header): "Copyright (C) 1994 Frank D. Cringle", **GNU GPL version 2 or (at your option) any later version**. It's fetched at test time, pinned by commit and sha256, and never committed (rule 9), as for the 8080 exercisers.
   - **Where from:** github.com/agn453/ZEXALL at commit 8f71d41 has `zexdoc.com` (8,704 bytes, sha256 `34923a7e…`) and its source `zexdoc.z80`, with a GPL v2 `LICENSE`. That repo's source is modified to assemble with ZSM4, so the original as shipped with yaze is in github.com/begoon/z80exer (`yaze/zexdoc.z80`, with `prelim.z80`). Which binary we pin (the prebuilt `.com`, or our own assembly of the original source) is for Homer to propose, with both hashes recorded.
   - It's a **CP/M program** (loaded at 0100H, output through BDOS calls at 0005H), so the test system needs the same CP/M stub as the 8080. The 8080 lesson applies: the stub must also give a correct top of memory at 0006H/0007H.
   - It masks the undocumented X/Y flags, which matches §1. `prelim.z80`, a quick pre-check like 8080PRE, is a candidate first step (same licence) [check its header].
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
- [x] 8-bit load group timing (PM pp.26–51, text layer): §6.1. Per-M-cycle bus types aren't in TM, PM, Mostek MK78515 or the 1987 TM, but **are in Mostek MK3880 Technical Manual §12 (Dec 1977)**: decision 7 → (a). NMI 11 T (5,3,3) and the mode 2 cycles from MK3880 p.83–84 (text layer). 8-bit load cycle types from MK3880 p.85 (page image); LD (IX+d),n is missing from that table. 16-bit load group: PM pp.52–75 and MK3880 p.85; MK3880's POP order contradicts PM p.72, and PM governs. Exchange/block group: PM pp.76–98 and MK3880 p.86; MK3880's EX (SP),IX length and its CPI row are corrected from PM. CPIR/CPDR termination (PM p.91). 8-bit arithmetic group: PM pp.99–130 and MK3880 p.86. General-purpose/CPU control and 16-bit arithmetic: PM pp.131–162, MK3880 pp.86–87. Rotate/shift and bit groups: PM pp.163–218, MK3880 pp.87–88; the DD CB op-byte read is a proposed Decision.
- [x] Flags, Table 6.0-1 (TM §6.0 pp.39–41, page image p.41): §6.2; the conflict with zexdoc's masks is open decision 6. Mostek MK78515 (Oct 1978) flag rows for CCF, LDI/LDD/LDIR/LDDR, CPI/CPIR/CPDR read: §6.2.
- [x] Reset (TM §3.0 p.9, §8.0 p.55, §11 p.70, text layer): what's reset and the 3-clock minimum. No post-reset timing in the TM, so §5 items 1–4 are Decisions.
- [x] Documented opcode set: PM Appendix C, 694 statements; omits LD R,A and LD A,R (and ED 63/6B), page image PDF p.304; ED 63/6B documented by PM pp.57, 62 (text layer, dd = HL listed): 698 forms, §6.0.
- [x] zexdoc licence: GPL v2 or later, © 1994 Frank D. Cringle (source header, agn453/ZEXALL@8f71d41, read 2026-11-18): §9.
