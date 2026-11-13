# tb/: testbench layout (Quinn)

Each test is a folder `tb/<name>/` with:
- `files.f`: RTL and testbench files, paths relative to the repo root.
- `tb.sv`: top module `tb`. Prints `PASS ...` and calls `$finish` on success. Prints `FAIL ...` lines and calls `$fatal` otherwise.

Run with `make test` (all) or `make test BLOCK=<name>`. Logs land in `logs/<run>/<name>.log`.

Expected values come from `docs/spec.md` only. The testbenches never read the RTL.

| Test | Covers |
|------|--------|
| `pg`, `carry`, `sum` | Each block against spec §3 (block split in `docs/blocks.md`) |
| `top_table` | Acceptance test 2 (TI function table, §4); B1, B2, B3, B5, B6, B8 |
| `top_exhaustive` | Acceptance test 1 (all 16,384 inputs vs §3); B1, B3, B4, B5, B8 |
| `top_cascade` | Acceptance test 3 / B7 (8-bit add and subtract, 65,536 pairs) |

Assumptions to confirm with Vera: the top module is named `top`, and the block modules are named `alu181_pg`, `alu181_carry`, `alu181_sum` with the port names in `docs/blocks.md`.
