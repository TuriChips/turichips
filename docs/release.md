# Release write-ups

One section per released chip, newest first. Every claim links to a log. If a number has no log, it does not go in.

No chips released yet. Copy the template below for each new chip.

---

## TEMPLATE: <Chip name> (<year of the original>)

**Status:** in progress / released (date)
**Card for the website:** name, year, one-line description, layout image (ideally our own render), link to this section.

### What it is
Two or three plain sentences for an outsider: what the original chip did and why it mattered.

### Try it
The one command that runs the demo from a fresh copy, and what you should see.
Demo output: <link to captured output in logs/>

### What we built
- Scope (what is in the chip, what is only a model in the testbench)
- Spec: <link to docs/spec.md at the release commit>

### Evidence
| Check | Result | Log |
|-------|--------|-----|
| Acceptance tests (named in the spec) | n of n pass | <link> |
| Spec behaviours with at least one test | n of n | <link> |
| Random tests vs reference model | n differences | <link> |

### Size and speed
| Metric | Value | Report |
|--------|-------|--------|
| Gate count / cells | | <link to synth/ report> |
| Longest path / max clock | | <link> |
| Original chip, for comparison | | <source> |

### What went wrong
Bugs verification found before release, spec mistakes, and anything the team got wrong. Link the issues.

### Manager interventions
Number of `needs-manager` issues for this chip: n (the lab's key KPI). List them.

### Credits and licences
Any outside tools used (as tools only), and confirmation that no original ROMs or copied code are in the repo.
