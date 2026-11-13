<p align="center"><img src="brand/logo-512.png" width="160" alt="Turichips logo"></p>

# Turichips

A one-person company staffed by AI agents.

- `COMPANY.md`: the shared document every agent reads first (agenda, what we're building, quarterly goals, KPIs).
- `agents/_rules.md`: rules every employee follows, who owns which folder, and the standup format.
- `agents/<role>.md`: one job description per agent. This is that agent's system prompt.

**How an agent starts:** its system prompt is `COMPANY.md` + `agents/_rules.md` + `agents/<role>.md`, in that order.

- `brand/`: the logo. `logo-original.png` is the source; `logo-square.png` and `logo-512.png` are trimmed and squared.
