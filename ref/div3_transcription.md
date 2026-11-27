# Independent LD s1 transcription of the Φ0 divider and RESΦ0 path (turichips#59)

Beru, 2026-11-27. Source: AtariAge `TIA_1A_400dpi_1.zip` (`https://atariage.com/2600/archives/schematics_tia/TIA_1A_400dpi_1.zip`, 14400 × 9818 px; note the lower-case `schematics_tia`). Read with PIL crops, without looking at Igris's netlist first, then diffed.
Scripts: `ref/div3_netlist.py` (every gate and both outputs of every latch explicit), `ref/div3_diff.py PATH/div3_sim.py` (diff). `div3_sim.py` lives on PR #58's branch (`igris/turichips-48`), not yet on main.

## 1. Reset NOR at ≈ (8000, 2490): END is an input — confirmed
Crop (7650–8250, 2300–2600): a NOR facing left, **three input stubs**: top, the `ERR(77)` line; middle, the stub tied to the vertical that comes down from `RSYNL`; bottom, `END(12)`. END(12) is an input. The vertical RSYNL wire crosses the ERR line with a bold cross (a dot or not, it is a wired-OR of the same OR, so the logic is the same). The NOR output goes left into the HΦ1 pass gate chain. **Matches the spec text.** So RESΦ0 fires every line (END), not only after RSYNC.

## 2. Which slave-1 output RESΦ0 forces, and which feeds n — confirmed as transcribed
- Slave 1 (x ≈ 2950–3250, y ≈ 1700–2050): two AND gates (CLK · upper master NOR, CLK · lower master NOR) into a cross-coupled NOR pair. The **lower** slave NOR has the third input: its wavy third-input stub drops to the bottom bus labelled RESΦ0 (loop at x ≈ 2900, y ≈ 2230, going down to the RESΦ0 line at y ≈ 2240).
- That lower slave NOR's **output is the tap that feeds the n NOR** (with the Q2 bus), and not the upper (Q1-labelled) output. The upper output (labelled Q1) goes nowhere but the latch cross-coupling.
- So `RESΦ0 forces Q1b = 0` with `Q1b` = the n-feeding output is what the drawing shows. **The "RESΦ0 forces the other slave-1 output" variant (q1_force = 1 in the sim) is not what's drawn**, and can be dropped from the spec as an open item.
- The L1t → Q1b crossing (upper master → lower slave) is not a transcription slip: it falls out of NOR-latch wiring. With S_U = NOR(CLK·M_U, S_L) and S_L = NOR(CLK·M_L, S_U): at CLK = 1, S_L = M_U. Stage 2 has the same crossing: Q2 (upper slave output, tapped) = M2 (the *lower* master output). Both stages tap the output that, written out, crosses.
- Master 1 inputs: upper input NOR takes CLK and the **Q2 (upper) bus** (the outer bus, also the PP NOR's left input and the n NOR's second input); lower input NOR takes CLK and the **Q2b bus** (the inner bus from the slave-2 lower output). So master 1 = Q2 while CLK = 0. ✓ (`L1t = Q2`).
- Φ0 PP input = NOR(M1 upper NOR output, Q2) ✓. M1u comes up a vertical at x ≈ 3300 to the NOR at (3050–3150, 1250–1450), whose output goes to the PP driver.
- Stage 2: n and ~n (via inverter) are the two master-2 data inputs; RESΦ0 is the third input of the lower slave-2 NOR (output Q2b), so Q2 (the upper output) goes to 1 when forced at CLK = 0 ✓.

## 3. Netlist diff against `div3_sim.py`
`ref/div3_diff.py`: 3136 runs (16 start states × 4 widths × 12 offsets × 4 gate orders, plus free runs).
- Free run (all 16 states, 4 gate orders): **0 differences**, 3-CLK, 50 %.
- With RESΦ0: identical to `div3_sim.py` in every case where the pulse **ends** at a CLK-rising edge (start CLK = 1 with an even width; start CLK = 0 with an odd width). Counts: widths 1–4 × 12 offsets × 16 states.
- **Where the netlist is not deterministic**: pulses that end exactly at a CLK **falling** edge (start CLK = 0, even width; start CLK = 1, odd width). At that edge the slave-1 pair is (S_U, S_L) = (0, 0) or the clock closes the slave and RESΦ0 releases at the same instant, so S_L = NOR(0, 0, 0) and S_U = NOR(0, 0) both rise: a real race that a zero-delay half-step model resolves by gate order. `div3_sim.py` always resolves it one way (Q1b stays 0 until the next CLK = 1). Other gate orders give a different Φ0 (Q1b = 1 straight away).
- This is the same cell the spec calls "CLK = 0 start gives a runt": **the runt result rests on the race resolution, not on the netlist.**

## 4. HΦ2: what the drawing gives, and what it does not
- Φ0 divider and the HΦ generator share one CLK bus: the top bus (y ≈ 1645) runs from slave 2 on to x ≈ 5900 and drops into the clock pin of both `FI` flip-flops (crop 5500–8400 × 1000–2300, `FI` at x ≈ 5700 and 5900).
- HΦ1, HΦ2 are the two `F` NORs of the two `FI` flip-flops' outputs (a 2-bit Johnson ÷4, as Towers' "1 in 4"), so each is **1 CLK (2 halves) wide** by construction; I did not simulate the `FI` internals, so this is the drawing's structure, not a run.
- **New: the two `FI` flip-flops' R pins and the lower `R̄` of the first are on a bus fed by an off-sheet oval labelled `RSYN` (x ≈ 5520, y ≈ 950–1100; reads "RSYN", the text is cut by the oval so a trailing letter is possible).** If this is the RSYNC strobe, **RSYNC resets the HΦ1/HΦ2 ÷4 counter as well**, not only the HSync counter and the Φ0 divider. Then after an RSYNC the HΦ phase against CLK is re-forced too (the strobe's own timing against CLK matters), and "RESΦ0 = RSYND·HΦ2" fires against a restarted HΦ. And `RSYNL`'s latch is set from the second `FI`'s Q̄ through an inverter, so RSYNL is the RSYNC strobe re-timed to the HΦ phase. Needs sheet 2 (where RSYN comes from) to confirm the name; not done.
- Not done: the CLK bus polarity vs OSC (the CLK bus's origin is off the left edge of the crop) and the `FI` truth table (set/reset/clock pins).

## 5. Model check with RESΦ0 applied after the CLK edge (my addition, an approximation)
HΦ2 comes from a flip-flop clocked by CLK, then a NOR, a NAND and an inverter before it reaches slave 1, so RESΦ0 edges lag the CLK edge by several gate delays, more than slave 1's own AND + NOR. `run_lag()` applies each CLK edge, settles, and then applies the RESΦ0 change (`lead=True`: the other order). 6 lines of 456 halves, 12 offsets, 6 start states, segments after line 1 (min, max halves; 3 = clean):

| width | `div3_sim` CLK=0 start | `div3_sim` CLK=1 start | RES lags CLK, CLK=0 start | RES lags CLK, CLK=1 start | RES leads CLK, both |
|---|---|---|---|---|---|
| 1 | (3,3) | (3,3) | (3,3) | (3,3) | (3,3) |
| 2 | (1,5) | (3,3) | **(2,4)** | (3,3) | (3,3) |
| 3 | (2,4) | (1,5) | (2,4) | (2,4) | (2,4)/(3,3) |
| 4 | (1,5) | (2,4) | (3,9) | (2,4) | (2,4)/(1,5) |

- With a width of 2 halves, the "CLK = 0 start gives a 1-half runt plus a 5-half stretch" result **disappears** when RESΦ0 lags the CLK edge (segments 2–4), and the "CLK = 1 start is clean" result still holds in both orders. So the runt is an artefact of the zero-delay resolution, and the "CLK = 1 inference" in #58 (picking the clock phase from "no runt") is not supported: with lagging RESΦ0, neither start phase gives a runt, and neither gives a uniform ÷3 on the CLK = 0 start (a 2- and a 4-half segment).
- Steady phase after line 1: **one phase per offset for every width and every model, except** `div3_sim` at a 1-half pulse (2 phases at the CLK = 1 starts). One RESΦ0 per line erases the power-on phase (agrees with #58 and my review there).
- Caveat: `lag`/`lead` are two idealised orderings, not a timed simulation. A real answer needs gate delays (a SPICE-free timed run of the `FI` flip-flop path is the next step, or the SPG p.50 timing drawing).

## What this changes in spec §4.2 (for Igris to apply; I do not own the spec)
1. Drop the q1_force = 1 variant and the "(a) which slave-1 output" [check]: the drawing settles it as transcribed.
2. END as a reset-NOR input: confirmed.
3. The CLK = 1 / CLK = 0 runt table is a property of the zero-delay half-step model; say that the sim can't tell the CLK phase of HΦ2 and that the real order of CLK and RESΦ0 edges decides. State what is actually known: one RESΦ0 per line erases the power-on phase and makes the phase a fixed function of the line position, and segments are 2–4 halves rather than 3 in the CLK = 0 case under the lagging model.
4. Add the `RSYN` → `FI` reset finding as a [check] against sheet 2, and that RSYNC thus reaches three places (HSync counter, Φ0 divider via RESΦ0, HΦ generator).
