# Blocks: 74181 4-bit ALU

Owner: Vera (Architect) · Spec: `docs/spec.md` · Status: ready for review

The chip is purely combinational. There are no clocks or resets.

| Block | File | Owner | Inputs | Outputs |
|-------|------|-------|--------|---------|
| `alu181_pg` | rtl/datapath/alu181_pg.v | Mira (B) | `a[3:0]`, `b[3:0]`, `s[3:0]` | `p[3:0]`, `g[3:0]` |
| `alu181_carry` | rtl/datapath/alu181_carry.v | Mira (B) | `p[3:0]`, `g[3:0]`, `cn_n` | `c[3:0]` (carry into each bit), `cn4_n`, `x`, `y` |
| `alu181_sum` | rtl/datapath/alu181_sum.v | Mira (B) | `p[3:0]`, `g[3:0]`, `c[3:0]`, `m` | `f[3:0]` |
| `top` (74181) | rtl/top.v | Theo (A) | `a[3:0]`, `b[3:0]`, `s[3:0]`, `m`, `cn_n` | `f[3:0]`, `cn4_n`, `x`, `y`, `aeqb` |

- Every equation is in `docs/spec.md` §3. Each block implements exactly its part of it.
- `top` connects the three blocks and computes `aeqb = &f`. Its port names and order must match spec §2 exactly, because tests bind to them.
- Theo's control-side share is small on this chip. That is expected for a dry run, since the point is to exercise the flow.
