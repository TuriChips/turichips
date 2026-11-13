<p align="center"><img src="brand/logo-512.png" width="160" alt="TuriChips logo"></p>

# TuriChips

The world's first chip lab run by AI. A team of AI agents designs, verifies and documents chips end to end, in simulation only. One human manager sets direction and merges pull requests.

- `COMPANY.md`: the shared document every agent reads first (agenda, what we're building, quarterly goals, KPIs).
- `agents/_rules.md`: rules every employee follows, who owns which folder, and the standup format.
- `agents/<role>.md`: one job description per agent. This is that agent's system prompt.

**How an agent starts:** its system prompt is `COMPANY.md` + `agents/_rules.md` + `agents/<role>.md`, in that order.

- `brand/`: the logo. `logo-original.png` is the source (black background); `logo-transparent.png` and `logo-512.png` have the background removed.

## Run a chip demo

> Not available yet. The toolchain (Otto) and the first chip do not exist, so there is no command to run. This section is filled in when chip #1 is released.

When it exists it will read like this:

```
git clone https://github.com/TuriChips/turichips
cd turichips
make demo CHIP=<chip>    # placeholder: the real command is set by Otto's toolchain
```

## Chips

| Chip | Year | Status | Write-up |
|------|------|--------|----------|
| (none released yet) | | | |

The order of chips is in `docs/roadmap.md`. Each released chip gets a write-up in `docs/release.md`.
