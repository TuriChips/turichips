# Blocks: Intel 4004 (Chip #1), DRAFT

Owner: Igris (Architect) · Spec: `docs/4004/spec.md` · Status: **DRAFT, not normative**, same gate as the spec (74181 released + Sai's sign-off). Moves to `TuriChips/chip-4004` with the spec.

All blocks are synchronous to the one rising-edge `clk` (spec §1). `reset` is synchronous, active high (spec §5). Only the pins of `i4004` (spec §2) and of `mcs4_system` are normative for tests. The internal ports below are the contract **between Zura and Ada**: tests don't bind to them, but neither designer changes one without a PR that the other reviews.

## 1. Block list

| Block | File | Owner | State it holds |
|-------|------|-------|----------------|
| `i4004_timing` | rtl/control/i4004_timing.v | Zura (A) | period counter |
| `i4004_control` | rtl/control/i4004_control.v | Zura (A) | instruction register, second-cycle flag (both cleared by reset, spec §5), `src_addr`, `ram_bank` |
| `i4004_alu` | rtl/datapath/i4004_alu.v | Ada (B) | `acc`, `cy` |
| `i4004_regs` | rtl/datapath/i4004_regs.v | Ada (B) | `r[0..15]` |
| `i4004_addr` | rtl/datapath/i4004_addr.v | Ada (B) | `slot[0..3]`, `sp` |
| `i4004` | rtl/top.v | Zura (A) | none (wiring only) |
| `i4001` | rtl/datapath/i4001.v | Ada (B) | 256 × 8 ROM, port latch, I/O state |
| `i4002` | rtl/datapath/i4002.v | Ada (B) | 4 × 20 × 4 RAM, port latch, I/O state |
| `mcs4_system` | rtl/control/mcs4_system.v | Zura (A) | none (wiring + bus resolution, spec §2/§7) |

## 2. Ports

### `i4004_timing` (Zura)
| Port | Dir | Width | Meaning |
|------|-----|-------|---------|
| `clk`, `reset` | in | 1, 1 | |
| `period` | out | 3 | 0 = A1 … 7 = X3 (spec §4). 0 while `reset` = 1, so the first edge after reset falls is A1 |
| `sync` | out | 1 | 1 exactly when `period` = 7 and `reset` = 0 |

### `i4004_alu` (Ada): `acc`, `cy` and every operation that writes them
| Port | Dir | Width | Meaning |
|------|-----|-------|---------|
| `clk`, `reset` | in | 1, 1 | `reset` clears `acc` and `cy` |
| `we` | in | 1 | On a rising edge with `we` = 1, `acc`/`cy` take the result of `op` |
| `op` | in | 5 | Table below |
| `b` | in | 4 | Operand: `R`, `M`, a status/port nibble or the immediate `D`, chosen by control |
| `acc` | out | 4 | Current `acc` |
| `cy` | out | 1 | Current `cy` |

`op` encoding:
| `op` | Operation (spec §6) | Used by |
|------|---------------------|---------|
| `00000` | none (`acc`, `cy` unchanged) | |
| `00001` | `{cy, acc} = acc + b + cy` | ADD, ADM |
| `00010` | `{cy, acc} = acc + ~b + ~cy` | SUB, SBM |
| `00011` | `acc = b`, `cy` unchanged | LD, XCH, BBL, LDM, RDM, RDR, RD0–RD3 |
| `1xxxx` | accumulator group with OPA = `xxxx`, exactly spec §6.4 (F0 CLB … FC KBP). `11101` (DCL), `11110`, `11111` (FE, FF): `acc`, `cy` unchanged | F0–FF |

So for OPR = 1111 control simply sends `op = {1'b1, OPA}`, and `b` is ignored.

### `i4004_regs` (Ada): the 16 index registers
| Port | Dir | Width | Meaning |
|------|-----|-------|---------|
| `clk`, `reset` | in | 1, 1 | `reset` clears all 16 (allowed by spec §5; tests still hold reset ≥ 64 edges) |
| `sel` | in | 4 | Register `R` = `r[sel]`. Pair = `P(sel[3:1])` |
| `r_data` | out | 4 | `r[sel]`, combinational |
| `r_inc` | out | 4 | `r[sel] + 1` mod 16, combinational (INC, ISZ) |
| `p_data` | out | 8 | `{r[2p], r[2p+1]}` with `p = sel[3:1]` (high nibble first, spec §3), combinational |
| `r_we` | in | 1 | Write `r_wdata` into `r[sel]` |
| `r_wdata` | in | 4 | |
| `p_we` | in | 1 | Write `p_wdata` into pair `sel[3:1]` (`p_wdata[7:4]` → `r[2p]`) |
| `p_wdata` | in | 8 | |

`r_we` and `p_we` are never 1 together (control guarantees it).

### `i4004_addr` (Ada): address stack, spec §3 circular model
| Port | Dir | Width | Meaning |
|------|-----|-------|---------|
| `clk`, `reset` | in | 1, 1 | `reset` clears `slot[0..3]` and `sp` |
| `pc` | out | 12 | `slot[sp]`, combinational |
| `inc` | in | 1 | `slot[sp] = slot[sp] + 1` mod 4096 |
| `load_low` | in | 1 | `slot[sp][7:0] = load_val[7:0]`, `slot[sp][11:8]` unchanged |
| `load_full` | in | 1 | `slot[sp] = load_val` |
| `push` | in | 1 | `sp = sp + 1`; with `load_full`, `slot[sp+1] = load_val` (JMS) |
| `pop` | in | 1 | `sp = sp − 1` (BBL) |
| `load_val` | in | 12 | |

At most one of `inc`, `load_low`, `load_full`, `pop` per edge, except `push` + `load_full` together. Because `pc` has already been incremented past the last word fetched, `pc[11:8]` *is* the "same page" of spec §6.2 (including the xFE/xFF quirk), so `load_low` needs no page logic.

### `i4004_control` (Zura): sequencing, decode, pins
| Port | Dir | Width | Meaning |
|------|-----|-------|---------|
| `clk`, `reset` | in | 1, 1 | |
| `period` | in | 3 | From `i4004_timing` |
| `test` | in | 1 | Pin (spec §4: sampled at the edge ending X3 of JCN's first cycle) |
| `d_in` | in | 4 | Pin |
| `d_out`, `d_oe` | out | 4, 1 | Pins, exactly spec §4 |
| `cm_rom`, `cm_ram` | out | 1, 4 | Pins, exactly spec §4 and §6.5 |
| `acc`, `cy` | in | 4, 1 | From ALU (for `d_out` at X2, JCN, and nothing else) |
| `pc` | in | 12 | From addr (A1–A3, and the page for FIN/JIN) |
| `r_data`, `r_inc`, `p_data` | in | 4, 4, 8 | From regs |
| `alu_we`, `alu_op`, `alu_b` | out | 1, 5, 4 | To ALU |
| `reg_sel`, `r_we`, `r_wdata`, `p_we`, `p_wdata` | out | 4, 1, 4, 1, 8 | To regs |
| `pc_inc`, `pc_load_low`, `pc_load_full`, `pc_push`, `pc_pop`, `pc_load_val` | out | 1 ×5, 12 | To addr |

Zura chooses the clock period in which each strobe fires. The only constraint is the pins: whatever control does inside a cycle, every pin in every period must match spec §4. Two points where that bites:
- RDM/RDR/ADM/SBM/RDn: the data is on `d_in` only during X2, so `alu_we` fires on the edge ending X2 with `alu_b = d_in` (or control latches `d_in` at X2).
- FIN: `reg_sel` must point at P0 (`sel` = 0000) while A1–A3 of the second cycle drive `{pc[11:8], P0}`, then at Pp when the data byte is written.

### `i4004` (Zura, rtl/top.v)
Ports exactly spec §2, in that order. Wiring only: instantiates the five blocks above and connects them by the names in this section. No logic.

### `i4001` (Ada): spec §7
Parameters: `CHIP` (4 bits, 0–15), `PORT_IN` (1 = port is input), `ROM_FILE` (string, `$readmemh`, 256 lines).
| Port | Dir | Width | Meaning |
|------|-----|-------|---------|
| `clk`, `reset` | in | 1, 1 | |
| `sync` | in | 1 | From the 4004. The ROM keeps its own period counter in step with it (period after `sync` = A1) |
| `cm_rom` | in | 1 | From the 4004 |
| `bus` | in | 4 | The resolved bus (spec §2), what every chip sees |
| `d_out`, `d_oe` | out | 4, 1 | What this ROM drives: OPR at M1 and OPA at M2 when it is the chip addressed at A3, and the port at X2 of RDR when it is the chip selected by the last SRC |
| `io_in` | in | 4 | Port pins, read when `PORT_IN` = 1 |
| `io_out` | out | 4 | Port latch, written by WRR when `PORT_IN` = 0; 0 after reset |

The ROM recognises an I/O instruction by `cm_rom` = 1 at M2 (spec §4 `io`), and SRC by `cm_rom` = 1 at X2.

### `i4002` (Ada): spec §7
Parameter: `CHIP` (2 bits, compared with `src_addr[7:6]`).
| Port | Dir | Width | Meaning |
|------|-----|-------|---------|
| `clk`, `reset` | in | 1, 1 | `reset` clears the SRC latch, the port latch and the RAM contents (spec §7) |
| `sync` | in | 1 | As for `i4001` |
| `cm_ram` | in | 1 | The one CM-RAM line this chip is wired to (its bank) |

The chip latches SRC only when `cm_ram` = 1 at X2, and acts on an I/O instruction only when `cm_ram` = 1 at M2 (spec §6.3, per-chip model).
| `bus` | in | 4 | Resolved bus |
| `d_out`, `d_oe` | out | 4, 1 | Drives M or S_n at X2 of RDM/ADM/SBM/RD0–RD3 when selected |
| `port_out` | out | 4 | Output port latch (WMP); 0 after reset |

### `mcs4_system` (Zura)
Parameters: `N_ROM` (1–16), `ROM_FILES` (one `$readmemh` file per chip), `ROM_PORT_IN` (16 bits, one per chip), `N_RAM_BANK0..3` (0–4 each).
| Port | Dir | Width | Meaning |
|------|-----|-------|---------|
| `clk`, `reset`, `test` | in | 1, 1, 1 | |
| `rom_io_in` | in | 4 × 16 | Port inputs, chip *n* at `[4n+3:4n]` |
| `rom_io_out` | out | 4 × 16 | |
| `ram_port_out` | out | 4 × 16 | Bank *b*, chip *c* at index `4b + c` |
| `bus` | out | 4 | Resolved bus, for tests and C2 |
| `bus_conflict` | out | 1 | 1 in any period where two or more drivers have `d_oe` = 1 (spec §2: the tests flag it) |

## 3. Who does what first
1. **Ada:** `i4004_alu`, `i4004_regs`, `i4004_addr` (no dependencies). Then `i4001`, `i4002`.
2. **Zura:** `i4004_timing`, then `i4004_control` and `i4004` against the ports above. Then `mcs4_system`.
3. **Titus:** C1–C8 testbenches on `mcs4_system` and `i4004` pins only.
4. **Beru:** reference model (instruction-level and pin-level), C9, acceptance test 3.
5. **Leo:** synthesis of `i4004` alone (the CPU is the chip; ROM/RAM are test fixtures, not synthesized).
6. **Homer:** demo (a decimal-addition program on `mcs4_system`) and `docs/release.md`.
7. **Tesla:** `chip-4004` repo from the toolchain template, pinned to the current toolchain.

These become issues titled `<Name>: <task>` in `TuriChips/chip-4004` when the gate opens.
