# Spec coverage: 74181 (Quinn)

Every behaviour in `docs/spec.md` §5 and the acceptance tests in §6, with the test that covers it.
A row counts as covered only once its test has a passing log in `logs/`.

| Spec item | Test(s) | Status |
|-----------|---------|--------|
| B1 f for all 32 functions, both cn_n | `top_table`, `top_exhaustive` | written, not yet run on real RTL |
| B2 logic mode ignores cn_n | `top_table` | written, not yet run on real RTL |
| B3 cn4_n both modes, worked example, comparator table | `top_table`, `top_exhaustive` | written, not yet run on real RTL |
| B4 x, y independent of m and cn_n | `top_exhaustive` | written, not yet run on real RTL |
| B5 aeqb == (f == 1111) | `top_table`, `top_exhaustive` | written, not yet run on real RTL |
| B6 comparator | `top_table` | written, not yet run on real RTL |
| B7 8-bit cascade | `top_cascade` | written, not yet run on real RTL |
| B8 no X/Z | `top_table`, `top_exhaustive` | written, not yet run on real RTL |
| Acceptance 1 (16,384 vs §3) | `top_exhaustive` | written, not yet run on real RTL |
| Acceptance 2 (TI table) | `top_table` | written, not yet run on real RTL |
| Acceptance 3 (cascade) | `top_cascade` | written, not yet run on real RTL |
| Block conformance | `pg`, `carry`, `sum` | written, not yet run on real RTL |
