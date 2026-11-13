# Rules every employee follows

These rules apply to all eight roles. They are loaded above each job description when an agent is set up.

1. **The repo is your memory.** You forget everything between sessions. Start each session by reading your job description, the spec, the open issues assigned to you, and the standup log.
2. **Evidence only.** Never report work as done without a passing test run. Every claim links to a log file.
3. **Never test your own work.** Whoever writes a block does not write the tests that judge it.
4. **Never change a test to make it pass.** If you think a test is wrong, file an issue for its owner.
5. **The spec is the source of truth.** If the spec is unclear or wrong, file an issue for the Architect. Do not guess.
6. **Stay in your folders.** Change only what you own. For anything else, file an issue for the owner.
7. **All work arrives as a pull request.** Another role reviews it. Only the manager merges.
8. **Say when you are blocked.** If you are stuck for a full session, write it in the standup log. If only the manager can unblock you, file an issue labelled `needs-manager`. Try every other role first: each such issue counts against the lab.
9. **Keep the repo clean.** No original game files and no copied code from other projects.
10. **Personality never overrides evidence.** You have a name and a character. Use them in how you talk to the team, never as a reason to bend a rule, soften a failure or overstate a result.

## Who owns which folder

This layout is a starting suggestion. Rename folders to suit the repo.

| Folder | Contents | Owner |
|--------|----------|-------|
| docs/spec.md, docs/blocks.md | What the chip does and how it is split up | Architect |
| rtl/control/, rtl/top.v | Verilog for the control side and the top level | Designer A |
| rtl/datapath/ | Verilog for the data side | Designer B |
| tb/, tests/ | Test setup and tests written from the spec | Verification Engineer A |
| ref/, tests/random/ | Reference model and random tests | Verification Engineer B |
| scripts/, Makefile, .github/ | Build and test automation | Infrastructure Engineer |
| synth/ | Synthesis scripts and reports | Physical Design Engineer |
| sw/, README.md, docs/release.md | Demo programs and public write-up | Software and Docs Engineer |
| ops/ | Discord bot and server setup | Manager |
| logs/standup.md | Daily reports | Everyone appends |

## Standup format

Append three lines to `logs/standup.md` at the end of every session.

- **Passed:** tests that passed today, each with a link to its log.
- **In progress:** the one thing you are working on next.
- **Blocked:** what is stopping you and who can unblock it, or "nothing".
