# Blocks: Zilog Z80 (Chip #4) — draft v0, not normative

Owner: Igris (Architect) · Spec: `docs/z80/spec.md` (draft, turichips#37) · Status: **draft**. The shared code tables (§2) get written once the spec's open decisions 6 and 7 are settled. The block split is proposed now so Zura and Ada can comment early.

**Clocking.** One model clock is **one half T state** (spec §4.0). Everything is synchronous to the rising `clk`, plus a phase bit `ph` (0 = the H half, Φ high; 1 = the L half, Φ low) kept by `z80_timing`. Edges the manual puts on Φ's falling edge (MREQ/RD fall mid-T1, WR mid-T2, read data in M2–M5, WAIT, HALT, BUSAK high) happen at the model edge that starts an L half. Rising-edge events happen at the edge that starts an H half. Pin outputs are registered per half, so every pin is stable for a whole model cycle, as compared (spec §4.0).

**Lessons applied up front** (8080: chip-8080#16, #20, #28, #37; 6502: chip-6502#9, #24, #31, #35, #39):
- Every mux select gets a code table here, not "control decides".
- Separate write enables for A and for F.
- A load path for a 16-bit address whose high byte arrives in the **same** cycle as the jump (JP nn, CALL, RET's SRH).
- Any opcode that control decodes from `ir` instead of the decode table is **listed here** (6502 #39).
- A latch whose input port is muxed by the top (like the 6502's `regs_din_tmp`) has its select signal in this contract (6502 #35).
- The data-bus source select reaches every register that is ever stored or pushed: A, F, B, C, D, E, H, L, IXH, IXL, IYH, IYL, PCH, PCL, and the TMP of read-modify-write.

## 1. Block list (proposed)

| Block | File | Owner | State it holds |
|-------|------|-------|----------------|
| `z80_timing` | rtl/control/z80_timing.v | Zura | M-cycle and T-state counters, the half phase `ph`, WAIT/Tw handling, BUSRQ/BUSAK state, the lengthened-cycle extras (spec §6.1) |
| `z80_decode` | rtl/control/z80_decode.v | Zura | none (combinational from the prefix state and `ir`: cycle plan row, ALU op, register selects; generated and checked by script against spec §6.0/§6.1, as the 6502's `gen_decode.py`) |
| `z80_control` | rtl/control/z80_control.v | Zura | IR, the prefix state (none / CB / DD / ED / FD / DD CB / FD CB), the cycle plan, IFF1, IFF2, IM, the NMI edge latch, the HALT state, TMP, the displacement latch |
| `z80_alu` | rtl/datapath/z80_alu.v | Ada | A, F, A', F' (the main/alternate AF swap of EX AF,AF'); 8-bit ALU, DAA, rotates and shifts, the BIT/SET/RES unit |
| `z80_regs` | rtl/datapath/z80_regs.v | Ada | B C D E H L and their alternates (the EXX swap), IX, IY, SP, PC, I, R (7-bit increment and bit 7 held), the 16-bit incrementer/decrementer and the address adder (IX/IY + d, PC + e) |
| `z80` | rtl/top.v | Zura | none (wiring, the address-bus and data-bus muxes, the output enables `bus_oe`/`d_oe`, spec §4.4) |
| `z80_mem` | rtl/datapath/z80_mem.v | Ada | 64 KiB RAM for tests (`$readmemh`), plus 256 I/O ports for the system |
| `z80_system` | rtl/control/z80_system.v | Zura | console port, the CP/M stub hook, WAIT/INT/NMI/BUSRQ stimulus, `bus_conflict` |

**Why the split differs from the 6502's:** the Z80 has an alternate register set (EX AF,AF' and EXX swap whole banks), 16-bit arithmetic, and indexed addressing with a signed displacement. So `z80_regs` owns a real 16-bit adder, while `z80_alu` stays 8-bit plus the flags. 16-bit ADD/ADC/SBC (§6.1, OCF IO(4) IO(3)) run as two 8-bit ALU passes over the IO cycles, low byte first. That's a proposal for Ada and Zura to accept or change.

## 2. Shared codes (control ↔ datapath)
To be written after decisions 6–7: `addr_sel` (PC, SP, HL, BC, DE, IX+d, IY+d, {I,R}, WZ-style temporary, the port {A or B, n or C}), `d_out_sel`, `alu_op`, `reg_wr` selects, `pc_op`, `sp_op`. Each will get a code table, in the 6502's format.

## 3. Ports
To be written with §2.
