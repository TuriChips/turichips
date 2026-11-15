# The chip story (STORY.md)

Every released chip gets two write-ups in its repo:

- **STORY.md**: for anyone. This is what the website shows. A curious person with no engineering background should finish it, understand what we built, and believe it works.
- **README.md**: for engineers. Run commands, repo map, the full evidence table, numbers. The story links to it at the end.

Homer owns both. The story is written last, from the README: every fact in the story is already in the README or a log.

## The reader

Picture a smart friend who has never heard of a logic gate. They read the whole thing on their phone in about six minutes (900 to 1,400 words). If they would have to google a word, explain it or cut it.

## Writing rules

1. **Every technical word is explained the first time, in plain words, or not used.** "ALU" becomes "the part of a computer that does the arithmetic". Words like RTL, netlist, sky130, testbench, DRC, X/Z do not appear; say what they mean instead ("the chip's design", "the version built from simple logic gates", "an open-source chip-making process").
2. **Make numbers relatable.** Compare to something a reader can picture: a grain of salt, a human hair, the year, a phone. Round them (about 2,300, not 2,312) unless the exact number is the point.
3. **Short paragraphs**, four lines at most. Write as "we", the lab.
4. **Every claim has proof.** End the sentence with a small link to the log: `([proof](logs/...))`. Plain language must never mean unverifiable. If there is no log, the claim does not go in.
5. **History facts have a source.** Link it the first time, the same rule as the spec. No dates, names or numbers from memory.
6. **Honest, never hyped.** No "revolutionary", no "perfect". Say what we did not do as plainly as what we did.
7. **The mistakes are the best part.** Tell them as small stories: what happened, how it was caught, what it taught us.
8. **Name the agents** when someone did something specific (Igris caught it, Beru broke it). Sai is the one human, and signs off the spec and the release.

## The outline

Use these sections in this order. Headings can be reworded to fit the chip; the order and the job of each section stay.

```markdown
# <Chip name> (<year>): <one plain line on what it is>

## The short version
Three or four sentences: what the chip is, that a team of AI agents rebuilt it,
and the single most vivid proof that it works.

Then three big numbers, one line each, in bold, each with a proof link. Pick the three a stranger will remember.

## Why this chip matters
The history as a story, with sources. Who made it, when, why, and what came after it because of it.

## What a chip like this actually does
One analogy-led explanation. What "4-bit" means, what an instruction is, what memory is for. Only as deep as
the reader needs to follow the rest of the story.

## How an AI team rebuilt it
The steps as a story: read the original manual or datasheet, write the rulebook (the spec), build the chip
from it, have other agents try to break it, turn it into a physical layout, Sai signs off.
Name who did what.

## The moment of truth
The most vivid demo: the chip running real software, doing a real job. Show the actual output.

## How we know it works
The README's evidence table, translated. Three to five checks in plain words, each with a proof link.
Always include the strongest one (checked against something we did not build) and how we tested the tests.

## What went wrong along the way
Two to four short stories, from the README's "What went wrong", each with its issue link.

## What it looks like
The layout picture with a caption a reader can follow (what the colours and shapes are), and one size
comparison against the original chip. Say that the processes differ, so the size gap is not our cleverness.

## What we did not do
One honest paragraph: simulation only, nothing manufactured, and anything else from the README's "Not done".

## Next up
One or two sentences on the next chip.

---
*For engineers: the full technical write-up, run commands and every log are in the [README](README.md).*
```

## Before you open the PR

- [ ] A non-engineer could read it without stopping. Read it once as that person.
- [ ] Every number matches the README or a log, and has a proof link.
- [ ] Every history fact has a source link.
- [ ] No unexplained jargon (search for: RTL, netlist, testbench, sky130, DRC, LVS, X/Z, Verilog, synthesis, flop).
- [ ] 900 to 1,400 words.
