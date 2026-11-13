# Spec: 74181 4-bit ALU (Phase 0 dry run)

Owner: Vera (Architect) · Status: **checked against the TI datasheet** (see §9)

The 74181 (TI, 1970) is a 4-bit arithmetic logic unit on one chip. It has 16 logic functions and 16 arithmetic functions, chosen by 5 control pins. We rebuild it to test our whole pipeline (spec → RTL → tests → synthesis → write-up) on a chip small enough to test exhaustively.

## 1. Scope
- **Purely combinational.** There is no clock, no state and no reset. Every output depends only on the current inputs.
- We use the **active-high data** convention throughout. The real chip can also be read with active-low data. That is the same silicon with relabelled pins, so we do not build or test it separately.
- **Out of scope:** electrical behaviour (voltages, fan-out, open-collector pull-up) and the 74182 lookahead carry chip.

## 2. Pins
All signals are 1 bit unless a width is shown. Bus bit 0 is the least significant bit.

| Signal | Dir | Width | Active | Meaning |
|--------|-----|-------|--------|---------|
| `a[3:0]` | in | 4 | high | Operand A |
| `b[3:0]` | in | 4 | high | Operand B |
| `s[3:0]` | in | 4 | high | Function select |
| `m` | in | 1 | high | Mode: 1 = logic, 0 = arithmetic |
| `cn_n` | in | 1 | **low** | Carry in. 0 = carry, 1 = no carry |
| `f[3:0]` | out | 4 | high | Result |
| `cn4_n` | out | 1 | **low** | Carry out (Cn+4). 0 = carry, 1 = no carry |
| `x` | out | 1 | see §3 | Lookahead output X (pin 15, for a 74182) |
| `y` | out | 1 | see §3 | Lookahead output Y (pin 17, for a 74182) |
| `aeqb` | out | 1 | high | A=B: 1 when `f == 4'b1111` |

The original 24-pin DIP numbering, for reference only (not tested): 1 B0, 2 A0, 3 S3, 4 S2, 5 S1, 6 S0, 7 Cn, 8 M, 9 F0, 10 F1, 11 F2, 12 GND, 13 F3, 14 A=B, 15 X, 16 Cn+4, 17 Y, 18 B3, 19 A3, 20 B2, 21 A2, 22 B1, 23 A1, 24 VCC.

`aeqb` is open-collector on the real chip. We model it as an ordinary output that drives 1 or 0.

## 3. Exact behaviour (normative)
These equations define the chip. If they disagree with the table in §4, the equations win, and an issue gets filed for Vera.

For each bit `i` in 0..3:
```
p[i] = a[i] | (b[i] & s[0]) | (~b[i] & s[1])        // bit propagate
g[i] = (a[i] & ~b[i] & s[2]) | (a[i] & b[i] & s[3])  // bit generate (g[i] implies p[i])
h[i] = p[i] & ~g[i]                                  // half-sum
```
Carries (active high, internal):
```
c[0]   = ~cn_n
c[i+1] = g[i] | (p[i] & c[i])        for i = 0..3
```
Outputs:
```
f[i]   = m ? ~h[i] : (h[i] ^ c[i])
cn4_n  = ~c[4]                                        // does NOT depend on m
x      = g[0] | g[1] | g[2] | g[3]                    // pin 15; does NOT depend on m or cn_n
y      = ~(~p[3] | ~g[3]&~p[2] | ~g[3]&~g[2]&~p[1] | ~g[3]&~g[2]&~g[1]&~p[0])   // pin 17; does NOT depend on m or cn_n
aeqb   = f[0] & f[1] & f[2] & f[3]
```
Notes:
- In logic mode (`m=1`), `f` ignores `cn_n`, but `cn4_n`, `x` and `y` are still computed as above. (In the datasheet logic diagram, M only gates the internal carries into the F outputs.)
- **Why X and Y, not P̄ and Ḡ.** The datasheet calls pins 15 and 17 P̄ and Ḡ only when the data is active-low (Figure 1). For active-high data it renames them X and Y (Figure 2, and the pin table on page 2). In active-high terms, with group generate `G = g[3] | p[3]&g[2] | p[3]&p[2]&g[1] | p[3]&p[2]&p[1]&g[0]` and group propagate `P = &p`:
  `y == G | P`, `x & y == G`, and `cn4_n == ~(y & (x | c[0]))`. That is exactly what a 74182 needs. The `x` and `y` equations above are read gate by gate from the datasheet logic diagram.
- Comparator use: with `s=0110`, `m=0`, `cn_n=1`, the chip computes A − B − 1, so `aeqb=1` exactly when `a == b`.

## 4. Function table (informative, active-high data)
`+` and `−` are 4-bit two's-complement arithmetic, mod 16. `|`, `&`, `^` and `~` are bitwise. "+1" means `cn_n = 0`.

| s3..s0 | m=1 (logic) | m=0, cn_n=1 | m=0, cn_n=0 |
|--------|-------------|-------------|-------------|
| 0000 | ~A | A | A + 1 |
| 0001 | ~(A\|B) | A\|B | (A\|B) + 1 |
| 0010 | ~A & B | A\|~B | (A\|~B) + 1 |
| 0011 | 0 | −1 (1111) | 0 |
| 0100 | ~(A&B) | A + (A&~B) | A + (A&~B) + 1 |
| 0101 | ~B | (A\|B) + (A&~B) | (A\|B) + (A&~B) + 1 |
| 0110 | A ^ B | A − B − 1 | A − B |
| 0111 | A & ~B | (A&~B) − 1 | A & ~B |
| 1000 | ~A \| B | A + (A&B) | A + (A&B) + 1 |
| 1001 | ~(A^B) | A + B | A + B + 1 |
| 1010 | B | (A\|~B) + (A&B) | (A\|~B) + (A&B) + 1 |
| 1011 | A & B | (A&B) − 1 | A & B |
| 1100 | 1111 | A + A | A + A + 1 |
| 1101 | A \| ~B | (A\|B) + A | (A\|B) + A + 1 |
| 1110 | A \| B | (A\|~B) + A | (A\|~B) + A + 1 |
| 1111 | A | A − 1 | A |

On 2026-11-13 I checked the §3 equations against this table with a throwaway script: all 16,384 (s, a, b, m, cn_n) cases for `f`, plus carry-out for A + B. There were 0 mismatches. This only shows the two sections agree with each other. It is not a datasheet check (see §9).

## 5. Behaviours to test
Every behaviour needs at least one test (Quinn), and the random/exhaustive check (Rook) covers all of them.

| ID | Behaviour |
|----|-----------|
| B1 | `f` matches §3 for all 32 functions (16 `s` × 2 `m`), for both values of `cn_n`. |
| B2 | In logic mode, `f` does not depend on `cn_n`. |
| B3 | `cn4_n` matches §3 in both modes. Example: A=1111, B=0001, s=1001, m=0, cn_n=1 → f=0000, cn4_n=0. |
| B4 | `x` and `y` match §3, and do not depend on `m` or `cn_n`. |
| B5 | `aeqb` is 1 exactly when `f == 1111`, in every mode. |
| B6 | Comparator: s=0110, m=0, cn_n=1 gives `aeqb == (a == b)` for all 256 (a, b) pairs. |
| B7 | Cascading: two 74181s, with `cn4_n` of the low chip wired to `cn_n` of the high chip, form a correct 8-bit adder (A + B and A − B) for all 65,536 operand pairs. |
| B8 | No X or Z on any output for any fully driven input. |

## 6. Acceptance tests
1. **Exhaustive check against the datasheet.** All 2^14 = 16,384 combinations of (a, b, s, m, cn_n), with every output compared against the §3 equations. The 74181 is small enough that nothing is sampled.
2. **TI function table.** Every row of the active-high function table in the TI SN74LS181 datasheet, checked against the RTL. This table comes from TI, not from us.
3. **Cascade test B7**, using two instances of our RTL.

Pass means every test passes with zero mismatches, with the logs in `logs/`.

## 7. Demo
An 8-bit calculator built from two cascaded 74181s in simulation, printing a few sums, differences and logic results (Juno).

## 8. Synthesis targets
No target, just measure: cell count and longest path from Yosys (Petra). For comparison, TI gives the chip "a complexity of 75 equivalent gates" (datasheet page 1).

## 9. Datasheet check
Source: Texas Instruments, *SN54LS181, SN54S181, SN74LS181, SN74S181 Arithmetic Logic Units/Function Generators*, SDLS136, December 1972, revised March 1988. Checked by Vera on 2026-11-13.

- [x] §4 matches Table 2 (active-high data), all 16 rows × 3 columns.
- [x] §2 pin numbers match the J/N package pinout (page 1) and the pin table (page 2).
- [x] `cn4_n` matches the comparator table (page 2). With s=0110 and m=0: cn_n=1 gives cn4_n=1 when A ≤ B and 0 when A > B; cn_n=0 gives cn4_n=1 when A < B and 0 when A ≥ B.
- [x] `x`, `y` and `cn4_n` are read from the logic diagram (page 5). The first draft wrongly used P̄/Ḡ equations on these pins. A script confirmed the corrected forms satisfy the three identities in §3 (0 mismatches).
- [x] M does not reach the lookahead outputs (logic diagram, page 5).
- [x] "75 equivalent gates" (page 1).
