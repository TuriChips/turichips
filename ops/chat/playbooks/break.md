## Playbook: break a PR (adversarial review)

Your job is to find the input that makes this change wrong. Your working copy is detached at the PR head; you can write scratch tests here, but pushing is turned off. Real new tests go in your own PR.

1. Read the diff and the spec. List the edge cases the author most likely missed: boundaries, flags, reset, timing, undocumented original-chip quirks.
2. Try to break it: run the existing tests, then write scratch tests or random programs against the reference model.
3. Leave one review with `gh pr review <n> -R <repo> --comment -b "..."`: each break with a reproducer, or what you tried that held.
4. Holds up: label `approved`, remove `review:<you>`. Broken: remove `review:<you>`, post the reproducer, and file an issue for the missing test in your own area if it should become permanent.
5. DONE with the PR ref and the verdict.
