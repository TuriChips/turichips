# Blocks: MOS 6502 (Chip #3), DRAFT

Owner: Igris (Architect) · Spec: `docs/6502/spec.md` · Status: **draft**, goes with the spec to Sai's sign-off and then to `TuriChips/chip-6502`.

All blocks are synchronous to the single rising-edge `clk`, one 6502 cycle per clock (spec §1). `res_n` is synchronous and active low (spec §5). Only the pins of `m6502` (spec §2) and of `m6502_system` are normative for tests. The internal ports below are the contract **between Zura (control) and Ada (datapath)**, and a port change needs a PR the other reviews.

**Lessons from the 8080's contract, applied up front** (chip-8080#16, #20, #28, #37):
- every mux select has a code table here, not "control decides";
- separate write enables for A and for flags;
- a load path for an address whose high byte arrives in the **same** cycle as the jump, as the 8080's `pair_op` 13;
- the data-bus source select can reach every register that is ever stored (A, X, Y, P, PCH, PCL);
- a TMP latch for read-modify-write.

## 1. Block list

| Block | File | Owner | State it holds |
|-------|------|-------|----------------|
| `m6502_timing` | rtl/control/m6502_timing.v | Zura | T-state counter (T0…T6), RDY hold, interrupt/reset sequence state |
| `m6502_control` | rtl/control/m6502_control.v | Zura | IR, the per-instruction cycle plan (§4.1), pending IRQ/NMI latches, the TMP latch |
| `m6502_alu` | rtl/datapath/m6502_alu.v | Ada | A, P (N V – B D I Z C storage, B as the push value only) |
| `m6502_regs` | rtl/datapath/m6502_regs.v | Ada | X, Y, S, PC (16), the address latches ADL/ADH (BAL/BAH, IAL/IAH reuse them) |
| `m6502` | rtl/top.v | Zura | none (wiring and the bus muxes) |
| `m6502_mem` | rtl/datapath/m6502_mem.v | Ada | 64 KiB RAM for tests (`$readmemh`), combinational read, write on the clock edge |
| `m6502_system` | rtl/control/m6502_system.v | Zura | console port, IRQ/NMI/RDY/SO stimulus inputs, `bus_conflict` |

## 2. Shared codes (control ↔ datapath)

`addr_sel` (3 bits), the source of `a`:

| code | `a` | used for |
|------|-----|----------|
| 0 | PC | opcode and operand fetches, implied dummy reads |
| 1 | {ADH, ADL} | absolute, indexed, and indirect targets |
| 2 | {00, ADL} | zero page and zero-page pointers (page-zero wrap, spec §4.1) |
| 3 | {01, S} | stack |
| 4 | {ADH, ADL} with ADH **uncarried** | the dummy read before a page cross (spec §4.1 A.2.5, A.3.6) |
| 5 | vector: {FF, Fx} | FFFA–FFFF (NMI/RES/IRQ, by `vec_sel`) |

`ab_op` (4 bits), the address-latch arithmetic in regs (8-bit adds, carry kept in `ab_carry` for the next cycle):

| code | operation |
|------|-----------|
| 0 | none |
| 1 | ADL ← `d_in` |
| 2 | ADH ← `d_in` |
| 3 | ADL ← ADL + X (8-bit, carry → `ab_carry`) |
| 4 | ADL ← ADL + Y (8-bit, carry → `ab_carry`) |
| 5 | ADH ← ADH + `ab_carry` |
| 6 | ADL ← ADL + 1 (8-bit, no carry: the zero-page pointer and the `JMP ($xxFF)` wrap, spec §6) |
| 7 | PC ← {`d_in`, ADL} (JMP abs, JSR: the high byte arrives in the jump's last cycle; the 8080 lesson) |
| 8 | PC ← {ADH, ADL} |
| 9 | PCL ← PCL + offset (branch, 8-bit, carry → `ab_carry`) |
| 10 | PCH ← PCH ± `ab_carry` (branch page cross, the sign from the offset) |

`pc_op` (2): 0 none, 1 PC + 1, 2 PCL ← `d_in`, 3 PCH ← `d_in` (RTS/RTI pulls).
`s_op` (2): 0 none, 1 S − 1, 2 S + 1, 3 S ← X (TXS).

`d_out_sel` (3 bits), the source of `d_out` on write cycles:

| code | value |
|------|-------|
| 0 | A |
| 1 | X |
| 2 | Y |
| 3 | P as pushed (B per `push_b`, bit 5 = 1; spec §3) |
| 4 | PCH |
| 5 | PCL |
| 6 | TMP (the RMW **unmodified** write) |
| 7 | ALU `result` (the RMW **modified** write, and INC/DEC) |

## 3. Ports (to be filled in per block, as the 8080's `blocks.md` §2)
- `m6502_alu`: `op` (5 bits: ADC SBC AND ORA EOR CMP CPX CPY BIT ASL LSR ROL ROR INC DEC LD, the flag set/clear ops), `b`, `a_we`, `f_we`, `pull_p`, `d_mode` (D flag in), `result`, `a_out`, `p_out`, `flags`. **Decimal-mode N/V/Z waits on spec §6's decision.**
- `m6502_regs`: `x_we`, `y_we`, `wdata`, `ab_op`, `pc_op`, `s_op`, `addr_sel`, `vec_sel`, `addr`, `ab_carry`, and debug `pc`, `s`, `x`, `y`.
- `m6502_control`: everything above, plus `rw`, `sync`, `d_oe` (= NOT `rw`, spec §4.0), the RDY hold, and the interrupt latches per spec §6.

## 4. Who does what first (when the spec is signed off)
1. **Ada:** `m6502_alu` and `m6502_regs` against §2–§3 here, then `m6502_mem`.
2. **Zura:** `m6502_timing`, then `m6502_control` and `m6502`, then `m6502_system`.
3. **Titus:** C1–C7 on the pins, with `tests/coverage.md` per spec §8.
4. **Beru:** the pin-level reference model and C8, with SingleStepTests as a cross-check (spec §9).
5. **Leo:** synthesis and sky130 layout.
6. **Homer:** Dormann's test runner (fetched, pinned), the demo, the write-up.
7. **Tesla:** the `chip-6502` repo and toolchain wiring.
