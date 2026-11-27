# Spec: Atari 2600 (TIA + RIOT), Chip #5: draft v0.2, not normative

Status: **draft.** Nothing here is normative until Sai signs off. Lines marked **[check]** still need a page (or a schematic zone) confirmed in §10. Choices that are ours, not Atari's or MOS's, are marked *Decision*. §3 lists the ones Sai rules on. Written by Igris for turichips#48. After sign-off it moves to `TuriChips/chip-2600` (repo to create), the same way the Z80 spec did.

## 1. Scope and sources

**What we rebuild:** the two custom/peripheral chips of the Atari Video Computer System (1977), at their pins:
- **TIA**: Television Interface Adaptor, model 1A, NTSC (Atari part CO10444 [check: the part number isn't printed in any source read so far]). Video timing, playfield, five movable objects, collisions, colour/luminance, two audio channels, six input ports, and the CPU clock and RDY.
- **RIOT**: MOS 6532 RAM-I/O-Timer. 128 × 8 RAM, two 8-bit ports with direction registers, the interval timer, and PA7 edge detection.

And around them, for tests and the demo only:
- **6507 CPU = the chip-6502 core, reused** (decision D1). The 6507 is a 6502 in a 28-pin package with A0–A12 only and no IRQ, NMI, SO or SYNC pins (SPG p.36, Figure 9: "MICROPROCESSOR 6507 28 PIN", "address bus (13)"). It is a library block, not new design: the Phase 2 pattern (`docs/roadmap.md`) one chip early.
- **The board**: address decode, a 4 KB cartridge ROM, the data bus with no pull-ups, controllers and console switches (§8). Board behaviour is specified because the acceptance tests depend on it, but it isn't "the chip" and isn't synthesised.

**Primary sources** (read locally, never committed):
- **SPG**: Steve Wright, *Stella Programmer's Guide*, 12/03/79, reconstructed by Charles Sinnett 6/11/93. 56 pages, with a text layer. Page numbers here are the printed ones (PDF page = printed + 5). Pages 17–51 are the **TIA 1A hardware manual** ("TIA 1A – Television Interface Adaptor (Model 1A)": detailed description, register bit maps, write/read summaries, timing drawings). The Atari datasheet the issue asks for is this section. Pages 12–15 cover the 6532 as wired in the console.
- **LD**: *TIA-1A Logic Diagram*, Atari, sheets 1–5, chip rev E, hand-drawn. Scanned by Mark De Smet and hosted on AtariAge (`2600/archives/schematics_tia/`: 2048-px and 400-dpi sets). Sheet 1: sync counter, playfield and motion registers. Sheet 2: data and address decode, collision register. Sheet 3: object and missile motion counters (×2). Sheet 4: audio circuits (×2). Sheet 5: colour-lum-priority circuits and the ball motion counter. Cited as "LD s<sheet> <zone>", for example LD s1 D5. This is the gate-level source. SPG's TIA section describes behaviour, but not to the colour clock.
- **RIOT DS**: *6532 (Memory, I/O, Timer Array)*, Commodore Semiconductor Group (MOS), datasheet 2/81, 10 pages, text layer plus page images. The 1976 MOS printing hasn't been found yet. The 1982 MOS Data Catalog (bitsavers) is a second copy to compare [check].

**Secondary sources**, cross-checks only, named where they're used:
- **Towers**: Andrew Towers, *Atari 2600 TIA Hardware Notes* v1.0, 6 March 2003. A reading of LD at the gate level: the counter decode tables, HMOVE, and the object start delays. Every number taken from it is marked [check: LD].
- **MVT**: the `missingno-vcs-tests` suite (§9). Each test's header states one behaviour, and the self-test verdicts were verified on a real console.
- Emulators (Stella, Gopher2600; both GPL) are not read for behaviour. Rule 9: no copied code.

**The rule when sources disagree.** LD rev E governs the TIA's colour-clock behaviour, RIOT DS governs the 6532, and SPG governs register meanings. A third-party test that disagrees with LD is a finding for Sai, like the Z80's zexdoc flag rows. It is never patched around silently.

**Scope proposals** (rulings in §3):
- NTSC TIA only. PAL and SECAM TIAs are different parts. SPG p.16 covers only their software side.
- Video is output as the digital values the TIA computes each colour clock: sync, blank, 3 luminance bits and the 4-bit colour code (§6.9). The analog colour phase shifter, colour burst waveform and DEL pad (LD s5) are not modelled (D4).
- Audio in scope as the two 4-bit digital levels (D5).
- No commercial game ROMs, ever (rule 9). The demo is our own program.
- Electrical timing is out of scope (SPG pp.46–51 ns tables, RIOT DS pp.3–5). We model clocks, not nanoseconds.

## 2. Pins

### 2.1 TIA (top module `tia`)
Package pads from LD (the pad boxes carry pad numbers), read from the 2048-px scans. **[check]** each against the 400-dpi set before sign-off.

| Port | Dir | Width | Pad | Meaning |
|------|-----|-------|-----|---------|
| `clk` | in | 1 | (OSC 11) | Model clock, two edges' worth per OSC cycle (D2, §4.1). The 3.58 MHz OSC is not a port |
| `rst` | in | 1 | none | *Model pin*: the TIA has no reset pad (LD: none on any sheet). Sets the power-on state of §5 |
| `phi0` | out | 1 | Φ0 4 | CPU clock = OSC ÷ 3 (SPG p.19 "divide by three counter … output (1.19 MHz) … pad called Φ0") |
| `phi2` | in | 1 | Φ2 26 | The CPU's Φ2. Writes latch "when the Φ2 clock goes from high to low", reads are valid "while the Φ2 clock is high" (SPG p.18) |
| `cs` | in | 4 | CS0 24, CS1 23, CS2 22, CS3 21 | Chip selects. In the console, CS0 = A12 and CS3 = A7, both selecting at 0 (connections from FSM Table 4-1, polarity from the memory map, §8.1). CS1 and CS2 are tied [check: LD s2 B7]. The board wiring is §8 |
| `rw` | in | 1 | R/W 25 | 1 = read |
| `a` | in | 6 | A0–A5 32…27 | Writes decode A0–A5 (45 decodes, LD s2 "WRITE ADDRESS DECODES"). Reads decode A0–A3 (LD s2 RA0–RA3) |
| `d_in` | in | 8 | D0–D5 14–19, D6 33, D7 34 | Write data |
| `d_out` | out | 2 | D6, D7 | Read data. Only D6 and D7 have tri-state drivers (LD s2 C7: "TRI-STATE DRIVERS, 2 PLACES") |
| `d_oe` | out | 2 | none | *Model pin*, one bit per line, 1 = TIA drives that line this half-cycle (§6.1) |
| `rdy` | out | 1 | RDY 3 | 0 = halt the CPU (WSYNC, §6.3) |
| `syn` | out | 1 | SYN 2 | Composite sync = HSYNC combined with the VSYNC bit (SPG p.18) |
| `blk` | out | 1 | BLK 6 | Blank |
| `lum` | out | 3 | L0 5, L1 8, L2 7 | Luminance code |
| `col` | out | 4 | (COL 9) | *Model*: the 4-bit colour code the phase shifter would encode (D4) |
| `aud0`, `aud1` | out | 4 each | (AUD0 13, AUD1 12) | *Model*: each channel's digital level (D5) |
| `inpt` | in | 6 | I0–I5 40…35 | Input port pins. I0–I3 are "dumped", I4–I5 "latched" (§6.8) |

Not modelled: DEL 10 (colour delay adjust), VCC 20, VSS 1.

### 2.2 RIOT (top module `m6532`), RIOT DS p.1 pin designation and pp.6–10
| Port | Dir | Width | Meaning |
|------|-----|-------|---------|
| `clk` | in | 1 | Model clock (D2, half an OSC period). |
| `ce` | in | 1 | Clock-enable, 1 for one model clock per Φ2 cycle (D3). Tied to the same CPU-cycle strobe as the core's `ce`, **not** gated by `rdy`: the timer and port logic keep running while WSYNC halts the CPU (MVT `riot/timer`: one scanline of TIM1T = 76 decrements through a WSYNC freeze) |
| `res_n` | in | 1 | RES: zeroes "all four I/O registers" (DDRs and output registers), floats the data bus, disables the PA7 interrupt and sets the negative edge (RIOT DS p.6, p.10). Timer and RAM are not named, so they are **not reset** (*Decision*, the 6502's convention; C-tests set them) |
| `cs1`, `cs2_n` | in | 1 each | Selected when CS1 = 1 and CS2 = 0 (RIOT DS p.10) |
| `rs_n` | in | 1 | RAM select: 0 = RAM, 1 = I/O and timer |
| `rw` | in | 1 | 1 = read |
| `a` | in | 7 | A0–A6 |
| `d_in` / `d_out` / `d_oe` | in / out / out | 8 / 8 / 1 | Data bus, split as for chip-6502 |
| `pa_in`, `pa_out`, `pa_ddr` | in / out / out | 8 each | Port A. Pins with DDR = 1 drive `pa_out`. The testbench resolves pin levels (§7.3) |
| `pb_in`, `pb_out`, `pb_ddr` | in / out / out | 8 each | Port B |
| `irq_n` | out | 1 | Open drain in the part. Not connected in the console (the 6507 has no IRQ pin) but specified and tested |

### 2.3 System (top module `a2600`, testbench-facing, not synthesised as "the chip")
`clk` (as TIA), `rst`, the cartridge port (`cart_a[11:0]`, `cart_d[7:0]`; ROM content loaded by the testbench), `swcha_in[7:0]` (joysticks, idle = 1), `swchb_in[7:0]` (console switches), `inpt[5:0]`, the TIA video and audio outputs, and debug taps of the CPU bus (`a[12:0]`, `d`, `rw`) for C-tests.

## 3. Decisions for Sai

**Ruled 2026-11-26 (Sai, #needs-sai: "approve all from my end"):** option (a), the recommended one, on D1–D10, and the hardware result on PA7 (§7.4: a polarity change does not set the flag, per MVT `riot/pa7-polarity`). Igris recorded this reading of "approve all"; Sai can overrule any item. The spec stays draft v0.2 until the remaining **[check]** items in §10 are closed.

Each one needed a ruling before v1. My recommendation is listed first.

| # | Question | Options (recommended first) | Governs |
|---|----------|-----------------------------|---------|
| D1 | What "the chip" is | **(a)** TIA + RIOT are the chip and get synthesis rows. The 6507 is chip-6502's core, pinned by commit (main `5c06fdc` today; chip-6502 has no tags yet), with A13–A15 unconnected, `irq_n`/`nmi_n`/`so_n` tied to 1 and `sync` unused. (b) Also count the 6507 as new work | §1, synthesis |
| D2 | Model clock resolution | **(a)** One model clock per **half** OSC period (456 per line). LD uses CLK and its inverse: MOTCK is "an inverted (out of phase) CLK" (Towers, [check: LD s1 C7]). Without half-periods, sub-colour-clock order can't be specified. This is the Z80's half-T lesson. (b) One per OSC period, if the LD reading shows that no observable signal changes on the falling edge | §4 |
| D3 | How the reused core is clocked | **(a)** Add a clock-enable `ce` to a library copy of `m6502` (`ce` = 1 for one model clock per CPU cycle). Rerun chip-6502's full test suite on the copy with `ce` tied to 1, per the block-library rule that a changed block re-runs every user's tests. (b) Feed the unmodified core a derived clock (a divided clock in the RTL; poorer for synthesis and timing). **D3b (RIOT):** the same `ce` goes to `m6532` (§2.2), tied to Φ2 and never to RDY. Option (b) would need the same derived clock there | §4.2, §2.2 |
| D4 | Video output | **(a)** Digital `syn`, `blk`, `lum[2:0]`, `col[3:0]` per colour clock. The frame dump is a 160-wide image of 7-bit codes, written as PNG through one fixed NTSC palette (testbench only, not compared). (b) Also model the colour-phase delay line | §2.1, §6.9 |
| D5 | Audio | **(a)** In scope. `audN` = AUDVN when the channel's output bit is 1, else 0, sampled at the audio clock. Checked by directed tests and Beru's model, since the acceptance suite has no audio tests. The demo also writes a WAV. (b) Out of scope: AUDxx registers latch and do nothing | §6.10 |
| D6 | Undocumented opcodes in the test ROMs. dasm's `macro.h` v1.11, which every MVT ROM includes, emits **LXA #0** (`$AB`) in `CLEAN_START` and **NOP zp** (`$04`) in `SLEEP n` for odd n, unless `NO_ILLEGAL_OPCODES` is defined. chip-6502 doesn't implement either | **(a)** Add to the core copy exactly `$04` (3 cycles: opcode, operand, read of the zero-page address, no register or flag change) and `$AB` with operand `$00` (A = X = 0, N = 0, Z = 1; other operands unspecified). Then the ROMs run as built and verified on hardware. Before ruling, scan the assembled binaries for any other undocumented opcode (Homer). (b) Assemble with `-DNO_ILLEGAL_OPCODES`. `bit VSYNC` then changes N, V and Z, and init takes 2 more cycles, so every test must be shown to be insensitive to that. (c) Drop the affected tests | §9, core copy |
| D7 | Power-on state | **(a)** `rst` puts every TIA latch and counter in one listed state (§5). Beru's random runs also start from random OSC÷3 and H-phase alignments, random object counters, and a random RIOT timer value and prescaler phase (§2.2 leaves them unreset), so that no acceptance result depends on one alignment. The hardware has no reset, and its phases at power-on are arbitrary | §5 |
| D8 | Which TIA | **(a)** LD rev E as drawn. Known revision differences (late-HMOVE behaviour varies between TIA revisions, per Stella issue #246) are out of scope. An MVT test that needs another revision's behaviour is a finding for Sai, not a design change | §1, §6 |
| D9 | Cartridge | **(a)** 4 KB (and 2 KB mirrored) ROM, no bank switching. MVT `cartridge/` (46 tests of mappers, DPC, Supercharger) is out of scope | §8, §9 |
| D10 | PAL arbiter. MVT's self-test verdicts were verified on an Australian **PAL** console (July 2026), but we model the NTSC TIA (§1). The self-tests are used as arbiters on the assumption that the PAL and NTSC TIA's colour-clock logic match, apart from line count and colour encoding, which the TIA doesn't count or check anyway | **(a)** Accept the assumption for self-tests and screenshots. A disagreement with LD that traces to PAL/NTSC is a finding for Sai. (b) Use MVT only for tests that are timing-independent of the TIA variant, with Beru's model as arbiter for the rest | §7.2, §7.4, §9 |

## 4. Clocks and timing

### 4.1 Colour clock and line (SPG pp.1, 4, 18; LD s1)
- OSC = 3.58 MHz colour clock ("CLK"). One colour clock = one pixel in the visible part of the line.
- A line is **228 colour clocks**: 68 of horizontal blank, then 160 visible (SPG p.1, p.4). The HSync counter "has a total count of 228. Blank is decoded as 68 counts and sync and color burst as 16 counts" (SPG p.18).
- The HSync counter is a 6-bit polynomial counter (LFSR) stepped once per 4 colour clocks by a two-phase clock H@1/H@2 derived from CLK (LD s1 D4–D3). It counts 57 states per line (57 × 4 = 228).
- **Counter (LD s1 D4–D3, 400-dpi scan read 2026-11-27):** six DIR stages Q1…Q6 shift towards Q6. The new Q1 = NOR(NOR(Q5, Q̄6), AND(Q5, Q̄6)) = **XNOR(Q5, Q6)**, so a reset to 000000 steps to 100000 (Q1…Q6 order). This is a maximal 63-state sequence, which the END decode cuts to 57. Towers' 63-row state table follows exactly this rule (checked by script: XNOR of his 5th and 6th bits reproduces all 62 transitions, and no other tap pair does).
- **Decodes (LD s1 "COUNTER DECODES"):** each decode row on the drawing carries its state in octal. The octal digits read Q6…Q1, so `12` = Q1…Q6 `010100`. Every label matches Towers' state for the same decode (script, 2026-11-27):

| Decode | LD label (octal) | Q1…Q6 | Count | CLK at start | Effect |
|--------|------------------|-------|-------|--------------|--------|
| SHS | 17 | 111100 | 4 | 16 | HSYNC on |
| RHS | 73 | 110111 | 8 | 32 | HSYNC off |
| RCB | 74 | 001111 | 12 | 48 | colour burst off |
| RHB | 16 | 011100 | 16 | 64 | HBLANK off (first visible pixel at CLK 68) |
| LRHB | 72 | 010111 | 18 | 72 | HBLANK off instead of RHB when the HMOVE latch is set (8 more blank pixels: the "HMOVE comb") |
| CNT | 15 | 101100 | 36 | 144 | centre: playfield restarts (copy or reflect) |
| END (SHB) | 12 | 010100 | 56 | 224 | HBLANK on, counter reset to 0, WSYNC released |
| ERR | 77 | 111111 | n/a | n/a | illegal state: reset to 0 |

  "Count" is the number of steps from 000000, and "CLK at start" = 4 × count, from the counter reset. Each decode's effect is delayed by one D1/D2 box (4 CLK, one counter step) after its state, unless noted; the "CLK at start" column is the state's time, so the first visible pixel at CLK 68 relies on this rule. Still [check: LD s1 C5–C4], because the phase per box is open.

- **END reset timing:** the reset acts on the DIR NOR reset input at the step out of state 56, so the counter goes 56 → 000000 and Q1…Q6 `101010` (count 57) never appears in a line. That gives 57 states × 4 = 228 CLK. If END's reset went through a D1 like the other decodes, the counter would sit at `101010` for one step (58 states, 232 CLK). Still [check: LD s1 C5–C4]: the route of END's reset.
- **Delay cells (LD s1 legend, D1–C1):** **D1** = pass gate → inverter → pass gate → inverter: one bit carried through both phases of the two-phase clock, so one counter step (4 CLK). **D2** = the same with a 2-input NOR in place of the first inverter (OR of two decodes, then delayed). **DIR** = a D1 whose second inverter is a NOR with a reset input (the counter stages). **DL** = a set/reset latch with the same two pass gates. The `*` nodes are the dynamic storage nodes. So the 4-CLK rule under the table is structurally right for decodes that go through one D1/D2. Still [check: LD s1 C5–C4]: which of H@1/H@2 gates each box's first pass gate (that fixes 4 vs 2 CLK per box), the phase of H@1/H@2 against CLK, and the route of each decode (some pass through two boxes).

  So pixel *x* (0–159) of a line without HMOVE is colour clock 68 + *x* from the SHB-reset origin.
- **Vertical timing is software's job**: VSYNC D1 and VBLANK D1 (SPG pp.4–5, p.37). The usual frame is 3 + 37 + 192 + 30 = 262 lines (SPG p.1), but the TIA neither counts nor checks lines. The model's frame boundary is the **falling** edge of the VSYNC latch (D4): a captured frame is every line after the VSYNC lines, 259 lines in the MVT reference PNGs. Homer's runner uses this one rule.

### 4.2 CPU clock and the bus (SPG pp.4, 18–19)
- Φ0 = OSC ÷ 3, so one CPU cycle = 3 colour clocks and a line is 76 CPU cycles (SPG p.4).
- Per D3, the 6502 core advances one cycle per Φ0 period. *Decision* (proposed): the CPU's Φ2 equals Φ0 with no delay (on the real board the 6507 makes Φ2 from Φ0 with a few ns of lag, which we don't model).
- TIA write: data and address are latched "when the Φ2 clock goes from high to low" (SPG p.18). The colour clock and half on which that edge falls within the 3-clock CPU cycle **[check: SPG p.46 "TIA Φ0..Φ2 and LUM timing" (hand-drawn page image) and LD s1 D7 "DIVIDE BY THREE", s2 B6 Φ2 path]**. Every RESPx, HMOVE and mid-line write result in §6 depends on this one alignment, so it is the first thing to settle.
- The divide-by-3 counter's phase relative to the H@1/H@2 clock is **not** established as free-running. **RSYNC and the HSync counter's own reset both reach the Φ0 divider** (LD s1 C6–D7, 400-dpi scan read 2026-11-27; reading corrected after Beru's review of turichips#56). The divide-by-3 is two master-slave stages of gated NOR latches (M1/Q1, M2/Q2). **Φ0 = PP(NOR(M1, Q2))**: a NOR (output bubble) of the stage-1 master's upper NOR output and the stage-2 output Q2, driven out through the PP pad driver to Φ0 (pad 4). The HSync reset NOR faces left at about (8000, 2490) px and has **three** inputs: ERR(77), END(12) and **RSYNL** (the latch the RSYNC write decode sets). Its output goes through an HΦ1-clocked pass gate and an inverter to a middle node (≈ 7350, 2490), then an HΦ2-clocked pass gate, an inverter and the E/A latch; the latch output is the counter reset. **RSYND is the wire tapped at that middle node**, so RSYND ≈ (ERR + RSYNL + END) delayed one HΦ1 stage, and the counter reset is the same signal delayed one more HΦ2 stage (so RSYNC resets the counter later, as Towers says). RSYND feeds a NAND whose inverted output is **RESΦ0**. The NAND's other input is **HΦ2**: it drops onto the lower of the two clock lines feeding the DL boxes, labelled HΦ2 at LD s1 C6 (HΦ1 is the upper line). So **RESΦ0 = RSYND · HΦ2**. RESΦ0 runs along the bottom of the divider and is a third input to the **lower NOR of both slave latches, Q1 and Q2** (Q1 entry at x ≈ 3100, Q2 entry at x ≈ 4820 px; Beru's re-read). **Consequence: because END and ERR are inputs to the reset NOR, RESΦ0 fires once every line (at END), not only after an RSYNC write.** So the Φ0-to-line phase may be re-forced every line whatever RSYNC does; whether that forcing is visible depends on the slave-latch gating during HΦ2. The SPG p.50 timing drawing is titled with the same chain, "RSYNC – RESΦ0 – HΦ1 – HΦ2 – SHB – Φ2 – Φ0". **Gate-level simulation** (Igris, 2026-11-27; netlist and script in `docs/2600/div3_sim.py`, which anyone can rerun). On the divider's CLK bus, the masters (gated NOR pairs) are transparent at CLK = 0 and the slaves (AND-into-NOR pairs) at CLK = 1. Netlist: master1 L1t = Q2 (L1t is the upper master NOR, Beru's "M1" above); slave1 Q1b = L1t; n = NOR(Q1b, Q2); master2 M2 = n; slave2 Q2 = M2; PP input = NOR(L1t, Q2). RESΦ0 forces Q1b = 0, and Q2 = 1 while CLK = 0. One RESΦ0 pulse = 2 halves (one HΦ2 pulse, Towers' 1-in-4 clock).
  - **Free run:** period 3 CLK with 50 % duty (1.5 high, 1.5 low), from all four starting states. That matches SPG p.19's "divide by three" and checks the transcription.
  - **One RESΦ0 normalises the phase.** The next rise of the PP input lands a fixed time after the pulse starts, whatever the phase before it: +6 halves if the pulse starts in a CLK = 0 half and +3 if in a CLK = 1 half (12 start positions).
  - **Independent check (Beru, turichips#59/#60, `ref/div3_transcription.md`):** END is a reset-NOR input (confirmed). RESΦ0 forces the lower slave-1 NOR, whose output feeds n, exactly as transcribed. Free run: 0 differences from `div3_sim.py` over 16 start states and 4 gate orders. With RESΦ0, the two agree whenever the pulse ends at a CLK rising edge. Where a pulse ends at a CLK **falling** edge, the netlist has a real race, and the zero-delay script resolves it by gate order. **The 1-half "runt" reported in #58 for a CLK = 0 start is an artefact of that resolution, so the inference built on it is withdrawn.**
  - **HΦ1/HΦ2 timing, from the drawing (LD s1 D5–C4 and the FI legend at C1, 400-dpi scan, 2026-11-28).** The HΦ generator is two **FI** flip-flops cross-wired as a 2-bit twisted ring (÷4). HΦ1 and HΦ2 are each an F-sized NOR of two ring outputs, so each is high for **1 CLK in 4**. The FI cell has the divider's own structure: S̄/R̄ gated by NOR with CK into a master NOR latch (transparent at CK = 0), then AND with CK into a slave NOR latch (transparent at CK = 1). Its CK pin is on the divider's CLK bus (Beru's report, §4). So **HΦ1 and HΦ2 change just after the same CLK rising edge as the divider's slaves**. RESΦ0 = RSYND · HΦ2 therefore **starts in a CLK = 1 half, a few gate delays after the edge, and lasts 2 halves**. In Beru's table that is the "RES lags CLK, CLK = 1 start, width 2" case, and it gives a clean 3-CLK Φ0 (3/3 halves) in both edge orderings.
  - **Result:** 456 halves = 76 × 6, so a free-running ÷3 already has the same phase against the line every line. The RESΦ0 at END adds two things: it **erases D7's random power-on phase after line 1**, and it **re-forces the phase after an RSYNC**. It makes no short or long cycles. So the colour clock of each CPU cycle's Φ2 edge is a fixed function of the cycle's position in the line. Which function is the §4.2 Φ2-edge check below.
  - **RSYNC reaches three places.** The off-sheet oval `RSYN` that drives the FIs' reset pins (found by Beru) is write decode **03** on LD s2 (the decode row's oval reads RSYN, address label 03 octal), so it is the RSYNC strobe. RSYNC therefore resets the HΦ ÷4 ring, the HSync counter (via RSYNL → the reset NOR) and the Φ0 divider (via RESΦ0). The RSYNL latch is set through an inverter from the second FI's Q̄, which re-times the strobe to the HΦ phase.
  - **The MVT `reset-phase` premise:** with Φ0 line-locked, skipping `CLEAN_START` doesn't give that test a different CPU-to-line phase after line 1. Whatever it probes comes from the strobe's position in the line, not from a free ÷3 phase (§9). The test is still run.
  - Still **[check]**: the ring state RSYN forces (so the HΦ phase after an RSYNC), the PP driver's polarity (which PP-input edge is Φ0's rising edge), and the CLK bus polarity against OSC. A timed (gate-delay) run would make the "lags" ordering a measurement, not an argument.

## 5. Reset and power-on (D7)
- TIA: no reset pad. With `rst` = 1 the model sets (*Decision*, proposed): every write register and latch to 0, HSync counter = 0 with H-phase = H@1 start, divide-by-3 phase = 0, object position counters = 0, the HMOVE "more motion" latches clear, collision latches clear, WSYNC/RDY released, audio poly counters to a stated non-illegal state [check: LD s4, which state the hardware can't lock in].
- RIOT: per §2.2 (`res_n`).
- 6507: chip-6502 §5 (reset vector at FFFC/FFFD, with A12–A0 mirroring it into the cartridge).
- System: `rst` holds TIA `rst` and RIOT `res_n` and the CPU's `res_n` together, for at least 2 CPU cycles (chip-6502's minimum [check]).

## 6. TIA behaviour

### 6.1 Registers (SPG pp.3, 18, 37–45)
- **Writes**: 45 addresses `$00`–`$2C`, decoded on A0–A5 (SPG p.44, LD s2). Writes to `$2D`–`$3F` do nothing. "There are no registers that are both read and write" (SPG p.18). Strobes act on the write and ignore the data.
- **Reads**: 14 addresses on A0–A3 (SPG p.45). The TIA drives only D7 and D6. Per MVT `cpu/partial-drive` (checked through the `$10/$20/$30` mirrors): INPT0–INPT5 drive **D7 only**, and the collision registers drive D7 and D6. CXBLPF's D6 ("most collision registers") is still **[check: LD s2 C6 "TRI STATE SELECTORS"]**. Lines the TIA doesn't drive keep the board's bus residue (§8). Read addresses with low nibble `$E`/`$F` drive nothing.

**Write map** (SPG p.44 for addresses, pp.37–43 for bits. The summary table on p.44 of the reconstruction has misplaced bit columns for AUDC0/1 and AUDF0/1; the detail pages govern: AUDC = D3–D0, AUDF = D4–D0, §10):

| Addr | Name | Bits | Addr | Name | Bits |
|------|------|------|------|------|------|
| 00 | VSYNC | D1 | 16 | AUDC1 | D3–D0 |
| 01 | VBLANK | D7, D6, D1 | 17 | AUDF0 | D4–D0 |
| 02 | WSYNC | strobe | 18 | AUDF1 | D4–D0 |
| 03 | RSYNC | strobe | 19 | AUDV0 | D3–D0 |
| 04 | NUSIZ0 | D5, D4, D2–D0 | 1A | AUDV1 | D3–D0 |
| 05 | NUSIZ1 | D5, D4, D2–D0 | 1B | GRP0 | D7–D0 |
| 06 | COLUP0 | D7–D1 | 1C | GRP1 | D7–D0 |
| 07 | COLUP1 | D7–D1 | 1D | ENAM0 | D1 |
| 08 | COLUPF | D7–D1 | 1E | ENAM1 | D1 |
| 09 | COLUBK | D7–D1 | 1F | ENABL | D1 |
| 0A | CTRLPF | D5, D4, D2–D0 | 20 | HMP0 | D7–D4 |
| 0B | REFP0 | D3 | 21 | HMP1 | D7–D4 |
| 0C | REFP1 | D3 | 22 | HMM0 | D7–D4 |
| 0D | PF0 | D7–D4 | 23 | HMM1 | D7–D4 |
| 0E | PF1 | D7–D0 | 24 | HMBL | D7–D4 |
| 0F | PF2 | D7–D0 | 25 | VDELP0 | D0 |
| 10 | RESP0 | strobe | 26 | VDELP1 | D0 |
| 11 | RESP1 | strobe | 27 | VDELBL | D0 |
| 12 | RESM0 | strobe | 28 | RESMP0 | D1 |
| 13 | RESM1 | strobe | 29 | RESMP1 | D1 |
| 14 | RESBL | strobe | 2A | HMOVE | strobe |
| 15 | AUDC0 | D3–D0 | 2B | HMCLR | strobe |
| | | | 2C | CXCLR | strobe |

**Read map** (SPG p.45): `0` CXM0P (D7 M0·P1, D6 M0·P0), `1` CXM1P (M1·P0, M1·P1), `2` CXP0FB (P0·PF, P0·BL), `3` CXP1FB (P1·PF, P1·BL), `4` CXM0FB (M0·PF, M0·BL), `5` CXM1FB (M1·PF, M1·BL), `6` CXBLPF (D7 BL·PF), `7` CXPPMM (P0·P1, M0·M1), `8`–`D` INPT0–INPT5 (D7).

### 6.2 Sync and blank (SPG pp.4–5, 18, 37)
- VSYNC D1 = 1 turns vertical sync on. `syn` = HSYNC combined with the VSYNC latch, polarity and combining gate **[check: LD s1 C8]**.
- VBLANK D1 = 1 forces blank. D6 enables the I4/I5 latches, D7 dumps I0–I3 (§6.8). "Disable latches (D6 = 0) also resets latches to logic true" (SPG p.37).
- `blk` = HBLANK (including the HMOVE extension) or VBLANK D1. While `blk` = 1, `lum` and `col` = 0 (SPG p.51 "LUM LINES = 000 = BLANK").
- RSYNC "resets the horizontal sync counter to define the beginning of horizontal blank time, and is used in chip testing" (SPG p.37). Exact timing (Towers: a full H@1–H@2 cycle after the strobe, the counter resets and HBLANK turns on) **[check: LD s1, SPG p.50/51 drawings]**. MVT `tia-timing/rsync` tests it, and `CLEAN_START` strobes RSYNC twice through the `$01xx` mirror (MVT README).

### 6.3 WSYNC and RDY (SPG pp.4, 19, 37; Figure 2 p.30)
- A write to WSYNC sets a latch that drives `rdy` = 0. The latch "is automatically reset to zero by the leading edge of the next horizontal blank timing signal" (SPG p.19).
- The 6502 core already stops only on read cycles with RDY = 0 (chip-6502 spec §2), so a `STA WSYNC` completes and the CPU halts on its next read. MVT `cpu/rmw-wsync` checks this.
- The exact colour clock of RDY release relative to SHB (SPG p.51 handwritten note: "READY LEAD TIME (if reset, ready will be set 5 osc cycles prior to horizontal blank time)") **[check: page image p.51 at higher resolution and LD s1 C8]**.

### 6.4 Playfield (SPG pp.5–6, 19–20, 38; LD s1 "PLAYFIELD REGISTERS")
- 20 bits: PF0 D4–D7, then PF1 D7–D0, then PF2 D0–D7, left to right. Each bit is 4 colour clocks wide. The left half of the line is drawn from those 20 bits, and the right half repeats them, or reverses them when CTRLPF D0 (REF) = 1 (SPG p.38 diagram).
- The serial output starts at RHB and restarts at CNT (§4.1). A PF register written while it is being scanned shows "part of the new value" on that line (SPG p.20). The exact colour clock from which a write is visible **[check: LD s1]**. MVT `tia-timing/midline-pf` is the screenshot test.
- CTRLPF D1 (SCORE): the playfield takes COLUP0 on the left half and COLUP1 on the right (SPG p.26, p.38). D2 (PFP): playfield and ball above players and missiles (SPG p.26).

### 6.5 Movable objects: position counters (SPG pp.8, 20–21, 39; LD s3, s5)
- Each of P0, P1, M0, M1 and BL has a 6-bit polynomial position counter with a period of 40 counts (160 colour clocks), clocked only in the visible part of the line by MOTCK (plus HMOVE's extra pulses, §6.6). So an object keeps its column from line to line (SPG p.20).
- **Decode matrices (LD s3 player and missile, s5 ball; 400-dpi scans read 2026-11-27).** These matrices carry no octal labels. They were read dot by dot: a pull-down on a stage's inverted column means that bit = 1, and on its true column, bit = 0. In Q1…Q6 order, the same order as §4.1:

| Row | Player (s3) | Missile (s3) | Ball (s5) | Count | Meaning |
|-----|-------------|--------------|-----------|-------|---------|
| 1 | 111111 | 111111 | 111111 | n/a | ERR: illegal state, reset |
| 2 | 101101 | 101101 | 101101 | 39 | wrap: reset to 000000 and start the main copy |
| 3 | 111000 | 111000 | none | 3 | copy start, "close" (+16) |
| 4 | 101111 | 101111 | none | 7 | copy start, "medium" (+32) |
| 5 | 111001 | 111001 | none | 15 | copy start, "wide" (+64) |

  Counts come from the §4.1 sequence. Each object counter's feedback gates are drawn as in §4.1 (Q5, Q6). Every row equals Towers' table (0 differences). The ball has only the ERR and wrap rows, which is SPG p.20's "only the zero crossing decode". A copy decoded at count *c* starts drawing one count later, so the offsets from the main copy (count 40 ≡ 0) are 4 × (*c* + 1) = 16, 32 and 64 colour clocks. Rows 3–5 also carry dots on four lines that aren't counter stages: each of the three rows carries two NZ dots, one on a line common to all three rows and one on a line of its own (read on the player matrix; the missile's row 5 is hard to read at this resolution). These are the NUSIZ number-select gating (NZ0/NZ1/NZ2 at LD s3 C4). Which NUSIZ codes enable which row is still [check: LD s3 "PLAYER NUMBER SELECT"]. The table below takes it from SPG p.39 and Towers.
- RESxx strobes reset that counter "at any time" (SPG p.20). Landing rule (MVT `collision/copy-adjacency` and `draw-delay`, **[check: LD s3, s5]**), in colour-clock pixels *x* where *s* is the strobe's pixel (colour clock − 68):
  - Player: first pixel = the later of *s* + 5 and (end of blank) + 3. Missile and ball: 1 earlier, *s* + 4 and (end of blank) + 2 (players start 1 clock after missiles and the ball).
  - Both arms are in pixels. End of blank is pixel 0 on a plain line, so the blank arm puts P at 3 and M/BL at 2. On an HMOVE line it is pixel 8 (§6.6, the comb), so P lands at 11 and M/BL at 10. Example: on an HMOVE line, a strobe at colour clock 75 (*s* = 7) puts P at max(12, 11) = 12. The strobe arm wins by one pixel.
  - Players in the stretched modes 101 and 111 start **one colour clock later** (MVT `tia-render/nusiz`: main copy at x = 18 in 1× modes, x = 19 in stretched modes).
  - A RESBL strobe starts the ball on the same line, at *s* + 4 (the rule above). After a RESPx/RESMx in the visible region, the **main copy** (the start at count 0) is not drawn until the counter wraps. The NUSIZ copies, decoded at counts 3, 7, 15 *before* the wrap, are still drawn on that line (reproducer: NUSIZ0 = %001, GRP0 = $FF, RESP0 near pixel 40: the close copy draws at reset + 5 + 16).
  - MVT `collision/reset-phase`: the landing also depends on the strobe's colour-clock phase inside the CPU cycle, not just on the CPU cycle (the fault sits at one strobe phase). It is not counted as coverage of this rule (§9, T5).
- NUSIZ D2–D0 (SPG p.39): copies and size, the same decodes for player and missile (SPG p.20):

| D2–D0 | Player | Copies at +0 and |
|-------|--------|------------------|
| 000 | one copy | none |
| 001 | two, close | +16 |
| 010 | two, medium | +32 |
| 011 | three, close | +16, +32 |
| 100 | two, wide | +64 |
| 101 | double size | none |
| 110 | three, medium | +32, +64 |
| 111 | quad size | none |

  Offsets: the decodes at counts 3, 7 and 15 are read from LD s3 (table above), giving 16, 32 and 64 colour clocks. Which NUSIZ codes enable each decode is still **[check: LD s3 "PLAYER NUMBER SELECT"]**. Missiles draw one copy in modes 101 and 111 (Towers, [check]).
- Players: GRPx is scanned D7 first, or D0 first with REFPx D3 = 1 (SPG p.41), 1, 2 or 4 colour clocks per bit (SPG p.22). Missile width NUSIZ D5–D4 and ball width CTRLPF D5–D4: 1, 2, 4 or 8 colour clocks (SPG pp.38–39).
- Enables: ENAMx D1, ENABL D1 (SPG p.41).
- RESMPx D1 = 1: the missile is disabled and its position is locked to "the center of its corresponding player" until D1 = 0 (SPG p.21, p.39). Mechanism: the missile counter is reset while the player's scan counter is at 4 during the main copy (Towers, [check: LD s3 "MISSILE TO PLAYER RESET"]).
- Vertical delay (SPG p.23–24): each player has a "new" and an "old" graphics register. Writing GRP0 copies P1's new to P1's old, writing GRP1 copies P0's new to P0's old **and** ENABL new to ENABL old. VDELPx/VDELBL D0 selects old.

### 6.6 HMOVE (SPG pp.8–9, 21, 40; LD s1 "MOTION REGISTERS")
- HMxx D7–D4 is a two's-complement motion, +7 (left) to −8 (right) (SPG p.40). HMCLR clears all five (SPG p.40).
- An HMOVE strobe applies all five at once. Mechanism (Towers, [check: LD s1]): it sets the HMOVE latch, which makes blank end at LRHB (+8 pixels, the comb) and is cleared at the line wrap. A 4-bit ripple counter runs 15 → 0 once every 4 colour clocks, and each object takes one extra clock pulse per step until its comparator matches (the D7 bit is compared inverted). Net motion = (HM ^ 8) − 8 pixels left.
- **Motion-register cells (LD s1 A8–B7, 400-dpi scan read 2026-11-27):** the 20 HMxx bits use two cell types. "Typical cell, 15 places" holds D4–D6 for 5 objects. "Typical cell, 5 places" holds the D7 row: its callout arrow points at that row (checked at 400 dpi: the lower "TYPICAL CELL 5 PLACES" arrow ends on the D7 row, the "15 PLACES" arrow on the D4–D6 block). Not to be confused with the second "TYPICAL CELL 5 PLACES" callout at the top left of s1, the H@1/H@2/SEC latch that feeds P0EC…BLEC. Both store D through a pass gate into a dynamic node (`*`), an inverter, and a NOR whose other input is HMCLR. Each drives a 2-transistor compare onto a 40/6 match line. The **only difference** is that the two compare transistors' gates are swapped: in the 15-place cell the upper one takes the inverter output and the lower one the NOR output, and in the 5-place cell the reverse. So D7 enters the compare in the opposite polarity to D4–D6. A match is a wired-NOR: a bit pulls the 40/6 line low when it equals the counter bit (pairs D̄·C̄ and D·C in the 15-place cell), so the line stays high, and the object gets another clock pulse, only while **all four bits differ** from the counter (D7 after its inversion). Reading "until it matches" as `counter == HM^8` gives motion 15 − (HM^8), backwards for every value except the midpoint. That is Towers' "D7 compared inverted", now from the drawing. Still [check: LD s1]: the 4-bit ripple counter, its start value and step phase, the per-object "more motion" latches and when the compare is sampled.
- SPG's constraints are programming advice, not limits of the model: "must immediately follow a WSYNC" and "should not be modified for at least 24 machine cycles after an HMOVE" (SPG p.9, p.21, p.40). The model computes whatever LD computes for every strobe time and every rewrite. That is how the late-HMOVE and stuck-motion results in MVT `tia-timing/hmove-*` (19 tests) arise.

### 6.7 Collisions (SPG pp.10, 24, 41, 45; LD s2)
15 latches, one per object pair (6 objects), set when both serial outputs are 1 on the same colour clock (SPG p.24). Gating (MVT `collision/blank-gating`, citing the TIA-1A schematic: "collision inputs are NANDed with the inverted VBLANK"): **only VBLANK D1 gates the latches**. HBLANK, the HMOVE comb and the stretched blank do **not**. Objects can fire inside HBLANK thanks to HMOVE's extra clocks. The `blk` output of §6.2 (HBLANK OR VBLANK) must not gate collisions **[check: LD s2]**. CXCLR clears all 15.

### 6.8 Input ports (SPG pp.11, 25, 37; LD s2 "INPUT PORTS")
- I0–I3: INPTn D7 = pin level, forced to 0 while VBLANK D7 = 1 (dump to ground). The analog RC charge time is the testbench's job: a paddle is a pin that goes to 1 some number of lines after the dump is released.
- I4–I5: with VBLANK D6 = 0, INPTn D7 = pin level. With D6 = 1, a latch that a 0 on the pin clears, and that stays 0 until D6 = 0 (SPG p.25). Writing D6 = 0 resets the latches to 1 (SPG p.37).

### 6.9 Priority and colour (SPG pp.5, 9, 26–27, 42; LD s5)
- Colour registers: D7–D4 = colour (hue) code, D3–D1 = luminance (SPG p.42). P0 and M0 take COLUP0, P1 and M1 take COLUP1, PF and BL take COLUPF, background takes COLUBK (SPG p.5).
- Priority (SPG p.26): normally P0/M0 > P1/M1 > PF/BL > BK. With PFP: PF/BL > P0/M0 > P1/M1 > BK. SCORE changes PF's colour as in §6.4. How SCORE and PFP combine for the ball **[check: LD s5 "PRIORITY ENCODER"; MVT `tia-render/score-mode`, `pf-priority`]**.
- Outputs per colour clock (D4): `lum` = D3–D1 and `col` = D7–D4 of the selected register, both 0 while `blk` = 1. Colour code 0 = no colour, 1 = gold (same phase as burst), 2–15 around the wheel (SPG p.27).

### 6.10 Audio (D5; SPG pp.10, 27–28, 42–43; LD s4)
- Each channel: AUDF D4–D0 divides an approximately 30 kHz clock by 1–32 (SPG p.42). AUDC D3–D0 selects the noise/tone mode of a 9-bit shift counter (SPG p.43 table, 16 modes). AUDV D3–D0 is the volume (SPG p.43).
- The 30 kHz clock is the audio clock AΦ1/AΦ2 decoded from the HSync counter, twice per line (LD s1 "AUDIO CLOCKS (Φ1–Φ2)"). Its exact counts **[check]**.
- The poly counters' taps and the mode decode come from LD s4. SPG's table names the modes ("4 bit poly", "div 31", …) but not the bits. **[check: LD s4 at 400 dpi]**.
- Output (D5 (a)): `audN` = AUDVN if the shift counter's output bit is 1, else 0.

## 7. RIOT behaviour (RIOT DS; SPG pp.12–15)

### 7.1 Addressing (RIOT DS p.10, Table 1)
RS = 0: RAM, A0–A6 select the byte. RS = 1:

| Op | A4 | A3 | A2 | A1 | A0 | Register | Console address (SPG p.15) |
|----|----|----|----|----|----|----------|---------|
| R/W | – | – | 0 | 0 | 0 | ORA / port A | `$280` SWCHA |
| R/W | – | – | 0 | 0 | 1 | DDRA | `$281` SWACNT |
| R/W | – | – | 0 | 1 | 0 | ORB / port B | `$282` SWCHB |
| R/W | – | – | 0 | 1 | 1 | DDRB | `$283` SWBCNT |
| W | 1 | IRQ en | 1 | div | div | timer, ÷1/8/64/1024 by A1A0 | `$294`–`$297` (+8 with IRQ enabled) |
| R | – | IRQ en | 1 | – | 0 | timer | `$284` INTIM |
| R | – | – | 1 | – | 1 | interrupt flags | `$285` |
| W | 0 | – | 1 | PA7 IRQ en | edge (0 = negative) | edge detect control | `$284`/`$285` |

### 7.2 Timer (RIOT DS pp.8–9, Figure 3 page image; SPG p.12)
- Write N to a timer address on Φ2 pulse 0 (the write cycle) with divide D. On pulse k, for 1 ≤ k ≤ N·D, the timer reads **N − ⌊(k − 1)/D⌋ − 1**. So it reads N − 1 from pulse 1 and steps down on pulses 1 + D, 1 + 2D, …. **The underflow is at pulse N·D + 1**: the timer goes to `$FF`, the timer flag sets, and from then on it decrements once per Φ2, reading `$FF` − (k − N·D − 1) (DS p.8, SPG p.12).
  - DS evidence: Figure 3 (52, ÷8) gives 25 at pulse 213 and 0 at pulse 415, which the formula reproduces. It also gives `10101100` = `$AC` at pulse 500 = `$FF` − 83, which only the N·D + 1 underflow reproduces. The DS text gives "total time to interrupt is (52 × 8) + 1 = 417T" (p.9), which agrees. Figure 3's item 4 ("interrupt has occurred at Φ2 pulse #416") is the one entry that doesn't: it puts the underflow a pulse early. The hardware result below arbitrates (D10).
  - Hardware evidence: MVT `riot/timer-vblank-spin` asserts the loop-count profile [46, 47, 47, 47, 47, 47, 48, 48] (codes $01–$08, verified on hardware). With the first INTIM read at pulse 29 + 2(8 − IDX) and 9 pulses per loop (no page crossing), this formula gives that profile. The v0.1 formula (N − ⌊k/D⌋ − 1, underflow at N·D) gives [46, 46, …] and fails code $02 (Beru's B9; rechecked by Igris with an independent script, 2026-11-26).
  - MVT `riot/timer-underflow-read` (hardware-verified): a read **on** the underflow pulse N·D + 1 returns `$FF` and leaves the flag set. A read one cycle later clears it.
- Timer edge cases R2 tests, with what is settled and what isn't:
  - N = 0: no special case. The underflow pulse N·D + 1 = 1, so the timer reads `$FF` and the flag sets at pulse 1. R2 tests it directly.
  - ÷1: the general rule with D = 1 (N − 1 at pulse 1, one step per pulse, `$FF` at pulse N + 1). That free-run passes `$00` again 256 pulses later. It wraps to `$FF` and keeps going, with the flag still set, **[check: DS p.8 says only that it counts "down to a maximum of −255T"; R2 tests 300+ pulses past underflow]**.
  - Read after underflow: clears the flag (DS p.9). It also ends the once-per-pulse free-run and goes back to ÷D. That comes from the MVT `riot/timer-divisors` header ("ends the post-underflow once-per-cycle free-run and re-arms the selected interval"). None of that test's codes ($01–$04) asserts it, so it's weaker evidence, and R2 checks it with a directed test. The pulse on which the ÷D counting resumes **[check: R2]**.
  - Prescaler on write: a timer write restarts the prescaler, so pulse 0 is the write. MVT `riot/timer-vblank-spin` relies on this (line 61: "arm: resets the 64-cycle prescaler to a known phase"), and its hardware-verified profile is deterministic only if the write sets the phase. DS Figure 3 also counts from the write.
- Flags (DS p.9, Figure 4): D7 = timer flag, D6 = PA7 flag, D5–D0 read 0. The timer flag clears when the timer is written or read, "however, the reading of the timer at the same time the interrupt occurs will not reset the interrupt flag" (DS p.9). Reading the flag register clears the PA7 flag only (DS p.9).
- `irq_n` = 0 while (timer flag and the timer IRQ enable) or (PA7 flag and the PA7 enable). The timer IRQ enable is A3 of the last timer write (DS p.8). Whether a timer read's A3 also changes it **[check: DS p.8 "During a Read or Write operation address line A3 controls the interrupt capability"]**.

### 7.3 Ports (RIOT DS p.6–7)
- DDR bit 1 = output. A port A read returns the **pin** levels: output pins read what is on the pin, input pins read the outside world. A port B read returns ORB for output bits (DS p.7: "allow the microprocessor to read the Output Register instead of reading the peripheral pin").
- Writing ORA/ORB stores all 8 bits whatever the direction (DS p.7). MVT `riot/io-output` tests this.
- In the console, Port A = joysticks (or paddle triggers or keyboard rows), Port B = console switches (SPG pp.13–15). Port B is "hardwired" as input by the board, not by the chip: SWBCNT is still a writable DDR [check: MVT `riot/io-ports`].

### 7.4 PA7 edge (RIOT DS p.7, p.10)
An active transition on PA7 sets the PA7 flag, "even if the pin is being used as … output", and also when the interrupt is disabled (DS p.7). Reset selects the negative edge with the interrupt disabled (DS p.10). Changing polarity may itself set the flag (DS p.7: "It may also be set by changing the polarity of the active interrupt"). MVT `riot/pa7-polarity` says this does **not** happen on the tested console. **Ruled by Sai 2026-11-26: follow the hardware (a polarity change does not set the flag); the datasheet says "may".**.

## 8. System (board) and behaviours to test

### 8.1 Board (FSM Table 4-1; MVT `riot/io-mirrors` and `ram-mirrors` headers)
**FSM**: Atari, *2600/2600A VCS Domestic (M/N) Field Service Manual*, FD100133 Rev. 02, January 1983 (vtda.org scan, 153 PDF pages, text layer). Table 4-1, "Connected Pins on Motherboard", p.4-47 (PDF p.88), lists every address and data line at the MPU (A200), TIA (A201), RIOT (A202) and cartridge connector (J200). The motherboard schematics themselves were a pocket insert and aren't in this scan.
- A12 = 1: cartridge, A0–A11. A 2 KB image is mirrored.
- A12 = 0, A7 = 0: TIA (writes A0–A5, reads A0–A3).
- A12 = 0, A7 = 1, A9 = 0: RIOT RAM (A0–A6). A12 = 0, A7 = 1, A9 = 1: RIOT I/O and timer.
- Wiring per FSM Table 4-1: **AB12 → TIA pin 24 (CS0) and RIOT pin 37 (CS2 per the RIOT DS; the FSM prints "37 (CS0)")**, **AB7 → TIA pin 21 (CS3) and RIOT pin 38 (CS1)**, **AB9 → RIOT pin 36 (RS)**. AB8, AB10 and AB11 reach only the MPU and the cartridge (pins 22, 19, 20), and AB6 isn't wired to the TIA. TIA A0–A5 = pins 32–27, D0–D5 = 14–19, D6 = 33, D7 = 34, which agrees with the LD pad numbers in §2.1. RIOT A0–A6 = pins 7–2 and 40, D0–D7 = 33–26. So the TIA is selected with A12 = 0 and A7 = 0, and the RIOT with A12 = 0 and A7 = 1, as the MVT headers say. Table 4-1 doesn't list TIA CS1 (23) and CS2 (22). In the model they're tied to their enabling levels **[check: a 2600 motherboard schematic; LD s2's rev E notes mention CS1/CS3 changes]**.
- **Bus residue** (*Decision*, proposed): the data bus has no pull-ups, so the model's bus holds the last value any chip or the CPU drove, per bit. A read cycle takes the TIA-driven bits from the TIA and every other bit from the residue (MVT `cpu/floating-bus`, `open-bus`, `partial-drive`).
- Idle inputs: `swcha_in` = `$FF`, `inpt[5:0]` = 1, `swchb_in` = `$0B` (colour, no switch pressed, both difficulties B [check: SPG p.13 bits]).

### 8.2 Behaviours to test (draft, C-tests for Titus, random for Beru)
- T1 HSync: 228-clock lines, the SHS/RHS/RCB/RHB/CNT/SHB colour clocks, `syn` and `blk` on every clock (§4.1, §6.2).
- T2 Φ0 = OSC/3 and the Φ2 write edge alignment (§4.2).
- T3 WSYNC: RDY low from the write to SHB, read-cycle-only halt; RSYNC.
- T4 Playfield: every bit at 4 clocks, copy and reflect, SCORE, PFP, mid-line writes.
- T5 Each object: RESxx in blank and at **every** strobe colour-clock phase in all 3 sub-cycle phases (we do not rely on MVT `reset-phase`, which tests one phase), NUSIZ copies and sizes, REFP, VDEL old/new copying, RESMP lock.
- T6 HMOVE: every HM value at the standard strobe, every strobe cycle across the line, rewrites during the 64-clock window, HMCLR.
- T7 Collisions: all 15 pairs, CXCLR, gating in blank.
- T8 Inputs: dump, latch, latch reset.
- T9 Priority and colour mux on every combination of the 6 serial outputs × PFP × SCORE.
- T10 Audio: all 16 AUDC modes × AUDF 0/1/31 against Beru's model for 2 full poly periods.
- R1 RIOT RAM, ports, DDRs. R2 timer: all 4 divides, N = 0, 1, 255, reads around underflow, flag clearing. R3 PA7 edges and IRQ.
- S1 Board decode and mirrors, bus residue.
- **C8-equivalent** (Beru): random 6507 programs (documented opcodes plus D6's two) writing random TIA/RIOT registers at random cycles, compared every colour clock on every output port against a reference model written from LD and RIOT DS, starting from random power-on phases (D7).

## 9. Acceptance tests

1. **missingno-vcs-tests** (MVT), github.com/ajoneil/missingno-vcs-tests, commit `891c079976a2f68033ca4af2fe2fd85aaf1906c9` (2026-08-09).
   - **Licence checked** (2026-11-26, `LICENSE` at that commit): **MIT, "Copyright (c) 2026 Andrew O'Neil"**. Fetched at test time, pinned by commit and sha256, never committed (rule 9), as for zexdoc.
   - **What it is**: one behaviour per ROM, each specified in its source header. "Verified on real hardware (an Australian PAL all-black unit, July 2026)". **Self-tests** write `$A5` (pass) or `$5A` (fail) to RAM `$80`, with the failing sub-check and its values at `$81`–`$83`. **Screenshot tests** compare one frame pixel-exact with `<test>_ntsc.png` (160 × 259, every line after the 3 VSYNC lines).
   - **In scope: 81 ROMs** (NTSC builds), 54 self-tests and 27 screenshot tests: `harness/` 2 (1 + 1), `cpu/` 7 (7 + 0), `riot/` 11 (11 + 0), `tia-render/` 15 (10 + 5), `tia-timing/` 30 (9 + 21), `collision/` 16 (16 + 0). All are 4 KB images at `$F000`.
   - **Out of scope**: `cartridge/` (46 ROMs: bank switching, DPC, Supercharger), per D9.
   - **Caveats for Sai**:
     (a) The NTSC reference PNGs are renders by the missingno emulator, aligned to captures from that PAL console. They are not NTSC hardware captures, and the console's TIA revision is unknown (D8). A screenshot mismatch where our design matches LD is a finding, not a failure to fix blindly.
     (b) Building the ROMs needs **dasm** (GPL-2.0, a build tool, not shipped) and its `vcs.h`/`macro.h` (licence text in those headers **[check]**, Homer). Or use the prebuilt binaries in github.com/ajoneil/missingno (MIT): Homer proposes which, with both hashes recorded, as for zexdoc.
     (c) D6: the ROMs as built contain `$AB` (LXA #0) and `$04` (NOP zp).
     (d) A screenshot needs a 7-bit code → RGB inverse map from the reference palette, and a rule for which frame is captured. Homer defines both from the MVT/missingno runner and records them in the runner.
   - **Not coverage**: `collision/reset-phase` passes at other strobe phases whatever the model does, so it isn't counted as evidence for object reset landing. T5 carries that. Its header skips `CLEAN_START` "on purpose". Per §4.2, Φ0 is line-locked from line 2 on whatever the power-on phase, so that choice doesn't change the CPU-to-line phase. The test still runs and must pass.
   - **Pass criterion**: all 54 self-tests reach `$A5` within a frame budget the runner states, and all 27 screenshots match. Runs go through `heavy` (they are full-system runs).
2. **Cross-check only**: SingleStepTests 65x02 (already used for chip-6502) on the core copy after D3/D6.
3. **Demo** (Homer): our own 2600 program, no commercial ROM. A title screen with playfield, two players, a moving ball and a tone, dumped as PNG frames (and a WAV if D5 (a)), and used for the website card.

## 10. Datasheet check
- [x] Line = 228 colour clocks, 68 blank + 160 visible; 3 colour clocks per CPU cycle; 76 cycles per line (SPG pp.1, 4, 18; text layer, read 2026-11-26).
- [x] Register addresses and bits (SPG pp.37–45, text layer). The reconstruction's write summary p.44 has wrong bit columns for AUDC0/AUDC1/AUDF0/AUDF1 (shows AUDC1 and AUDF0 as 5 bits, AUDC0 and AUDF1 as 4). The detail pages p.42–43 (AUDF D4–D0, AUDC D3–D0) govern [check: compare with the original 1979 page images if found].
- [x] Read map, D7/D6 only (SPG p.45). Only D6 and D7 have tri-state drivers (LD s2 C7, 2048-px scan).
- [x] WSYNC/RDY release at the leading edge of horizontal blank (SPG p.19, p.37).
- [x] RIOT addressing, timer, flags and PA7 (RIOT DS pp.6–10, text layer; Figure 3 timer timing and Figure 4 flags from the page image p.9).
- [x] LD sheet titles, rev E, and pad numbers in §2.1, read from the 2048-px scans 2026-11-26. [check] at 400 dpi.
- [x] RSYNC → RESΦ0 (§4.2): NOR(ERR, RSYNL, END) → HΦ1 stage → **RSYND** (middle tap) → HΦ2 stage → latch → counter reset. RESΦ0 = RSYND · HΦ2 (NAND + inverter) into the lower NOR of both slave latches (Q1 and Q2). Φ0 = PP(NOR(M1, Q2)). RESΦ0 fires on END/ERR every line, not only on RSYNC. LD s1 400-dpi scan, 2026-11-27; corrected after Beru's review.
- [x] Φ0 divider gate-level simulation (§4.2): 3-CLK, 50 % free run; one RESΦ0 sets a fixed phase; once per line it erases the power-on phase, and is runt-free only under the [check] conditions in §4.2 (Q1 polarity, HΦ2 width and phase). `docs/2600/div3_sim.py` (includes the per-line sweep), LD s1 400-dpi scan, 2026-11-27.
- [x] HΦ1/HΦ2 and the slave-1 forced output (§4.2): an FI twisted-ring ÷4 on the divider's CLK bus, each phase 1 CLK in 4, changing after the CLK rising edge. So RESΦ0 starts in a CLK = 1 half and the per-line RESΦ0 gives a clean, line-locked Φ0 (Beru's lagging model). The slave-1 forced output is as transcribed. The runt inference is withdrawn (race artefact, Beru #60). RSYN = write decode 03 (LD s2) resets the ring. LD s1/s2 400-dpi scans, 2026-11-28.
- [ ] **First:** the ring state RSYN forces, the PP polarity (§4.2); and the Φ2 write edge vs colour clock (§4.2): SPG p.46 + LD s1/s2. Everything mid-line depends on these.
- [x] HSync counter (§4.1): the feedback is XNOR(Q5, Q6), and the 8 decode labels (octal 17, 73, 74, 16, 72, 15, 12, 77) are SHS/RHS/RCB/RHB/LRHB/CNT/END/ERR at counts 4/8/12/16/18/36/56. Read from the LD s1 400-dpi scan (AtariAge `TIA_1A_400dpi_1.zip`, 14400 × 9818), 2026-11-27, and cross-checked by script against Towers' table: 0 differences.
- [ ] The 4-CLK decode latch delays and the H@1/H@2 phase (§4.1), and RSYNC (§6.2): LD s1.
- [x] Object position-counter decodes (§6.5): player and missile have 5 rows each (ERR, wrap at 39, copies at 3/7/15), the ball has 2 (ERR, wrap). Read dot by dot from the LD s3 and s5 400-dpi scans (AtariAge `TIA_1A_400dpi_3.zip`, `_5.zip`), 2026-11-27: 0 differences from Towers.
- [ ] Object reset landing, start delays, NUSIZ → decode enables, missile copies in modes 101/111, RESMP (§6.5): LD s3, s5.
- [x] HMOVE D7 inversion (§6.6): the 5-place cell (D7 row) swaps its two compare-transistor gates against the 15-place cell (D4–D6). LD s1 400-dpi scan, 2026-11-27.
- [ ] HMOVE ripple counter, "more motion" latches and compare timing (§6.6): LD s1.
- [ ] Collision gating (§6.7), priority with SCORE/PFP (§6.9): LD s2, s5.
- [ ] Audio clock and poly counters (§6.10): LD s1, s4.
- [ ] RDY lead time (§6.3): SPG p.51 page image, LD s1.
- [x] Board decode (§8.1): FSM FD100133 Rev. 02 Table 4-1, p.4-47 (PDF p.88, text layer), read 2026-11-27. A12 → TIA CS0 and RIOT pin 37, A7 → TIA CS3 and RIOT CS1, A9 → RIOT RS. The TIA/RIOT address and data pin numbers agree with §2.1 and RIOT DS p.1.
- [ ] TIA CS1/CS2 tie levels (§2.1): needs a 2600 motherboard schematic (FSM pocket insert, not in the scan).
- [x] Timer count and underflow pulse (§7.2): DS p.9 ("417T", Figure 3 items 2, 3, 5 from the page image) and MVT `riot/timer-vblank-spin` (hardware profile, simulated 2026-11-26) agree on underflow at pulse N·D + 1. DS Figure 3 item 4 ("#416") is the outlier. Still open: the ÷1 second wrap and the pulse on which ÷D resumes after a read (R2).
- [x] 1982 MOS Data Catalog (bitsavers), 6532 pp.2-107 to 2-116, compared with the 2/81 datasheet on 2026-11-27: the same text, including Figure 3 ("#416", items 2, 3 and 5) and "(52 × 8) + 1 = 417T". It's a second printing, not an independent source, so §7.2's evidence is unchanged.
- [ ] The CO10444 part number; the 1976 MOS 6532 printing.
- [x] MVT licence: MIT © 2026 Andrew O'Neil (LICENSE at 891c079, read 2026-11-26). The in-scope tests use no undocumented opcode in their own source (grep, 2026-11-26). The dasm macros do (D6).
