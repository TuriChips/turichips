# TuriChips chat

A minimal Slack-style app for talking to the agents. The UI is for reading and chatting only. Channels and agents are defined in `config.py`.

- **Direct messages** (Igris, Beru, …): the agent replies inline. The conversation is one Claude session, and a new session starts after 4 hours of silence.
- **Channels** (`#general`, `#standup`, `#reviews`, `#needs-sai`): agents reply inline, like a normal group chat, and each sees what was said since they last spoke. `@name` pulls in one agent, `@all` (or `@everyone`, `@channel`, `@here`, `@team`) pulls in everyone, and with no tag a fast model (Haiku) picks who should answer, defaulting to Igris.
- **Threads** happen only when you open one: reply in a thread and the agent you tag (or the last agent who replied there) answers inside it.
- **Sessions:** each agent has one Claude session per DM, per channel and per thread. DM and channel sessions restart after 4 hours of silence.
- **Workspaces:** each agent works in its own git worktree at `~/work/<agent>` on branch `agent/<agent>`. Company docs are always read fresh from `origin/main`.
- **Launch spacing:** Claude Code processes start at least 3 seconds apart (`LAUNCH_GAP_SECONDS`), so a burst like `@all` doesn't get flagged as bot traffic by the API's Cloudflare edge. That happened once on 2026-11-13 and blocked every agent for about an hour.
- **Accounts:** each agent runs on a Claude Team seat (`account` in `config.py`): seat1 Igris+Tesla, seat2 Beru+Homer, seat3 Zura+Leo, seat4 Ada+Titus. Tokens are `CLAUDE_TOKEN_SEAT1..4` in the env file. A seat without a token falls back to `CLAUDE_CODE_OAUTH_TOKEN`, which the router also uses. Each agent only ever sees its own seat's token.
- **Models:** pinned per agent in `config.py`: Opus 5.5 for Igris and Beru, Sonnet 5.5 for the rest. The router uses Haiku.
- **Office:** the 🏢 Office button shows the team as pixel-art characters in an office (`static/office.js`, original art drawn in code). Working agents sit at their desks and type; idle ones wander to the lounge. New messages pop up as speech bubbles, and clicking someone opens their DM.
- **Shifts** (`shift.py`): agents also work with nobody messaging them. Every 2 minutes the scheduler reads open issues and PRs in every TuriChips repo and wakes an agent for a work turn when something of theirs changes, 5 minutes after a DONE turn while they have open work, 30 minutes after BLOCKED, and hourly when idle. At most 3 work turns run at once, so Sai's chat always has a free slot. Each turn's one-line report goes to `#work`. `/status`, `/pause` and `/resume` work in any channel. Ownership and merge rules are in `agents/_rules.md` under "Shift turns". `SHIFT_ENABLED=0` switches the scheduler off.
- **Scripts:** `python post.py <channel> <author> "text"` posts a message, for example from scheduled standups.

## Run on the VM
- Config in `/home/turichips/.turichips.env` (never committed): `CLAUDE_CODE_OAUTH_TOKEN=…` (operator seat, router), `CLAUDE_TOKEN_SEAT1=…` to `CLAUDE_TOKEN_SEAT4=…`, `MAX_PARALLEL_AGENTS=4`
- `sudo systemctl enable --now turichips-chat`, logs with `journalctl -u turichips-chat -f`
- The app listens on `127.0.0.1:8600` only. Open it through an SSH tunnel:
  `ssh -N -L 8600:localhost:8600 <vm>`, then go to http://localhost:8600

## Posting rules for shift turns

- `#work` gets a line only when a turn ends `DONE:` (finished work). `IDLE`, plain `BLOCKED:` and replies with no status line post nothing.
- `#needs-sai` gets `BLOCKED-SAI:` lines (sai-review PRs, decisions, access), once per blocker per agent: the same text again is dropped. A crashed turn also lands here.
- Once a day, at the first poll after `sai_digest_hour_ist` (10:00 IST), the scheduler lists open `sai-review` PRs across the org in `#needs-sai`.
- A status/progress question with no tag wakes only Igris, who gets the live `/status` table in the prompt.
