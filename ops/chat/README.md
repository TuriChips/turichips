# TuriChips chat

A minimal Slack-style app for talking to the agents. The UI is for reading and chatting only. Channels and agents are defined in `config.py`.

- **Direct messages** (Vera, Rook, …): the agent replies inline. The conversation is one Claude session, and a new session starts after 4 hours of silence.
- **Channels** (`#general`, `#standup`, `#reviews`): agents reply inline, like a normal group chat, and each sees what was said since they last spoke. `@name` pulls in one agent, `@all` (or `@everyone`, `@channel`, `@here`, `@team`) pulls in everyone, and with no tag a fast model (Haiku) picks who should answer, defaulting to Vera.
- **Threads** happen only when you open one: reply in a thread and the agent you tag (or the last agent who replied there) answers inside it.
- **Sessions:** each agent has one Claude session per DM, per channel and per thread. DM and channel sessions restart after 4 hours of silence.
- **Workspaces:** each agent works in its own git worktree at `~/work/<agent>` on branch `agent/<agent>`. Company docs are always read fresh from `origin/main`.
- **Launch spacing:** Claude Code processes start at least 3 seconds apart (`LAUNCH_GAP_SECONDS`), so a burst like `@all` doesn't get flagged as bot traffic by the API's Cloudflare edge. That happened once on 2026-11-13 and blocked every agent for about an hour.
- **Models:** pinned per agent in `config.py`: Opus 5.5 for Vera and Rook, Sonnet 5.5 for the rest. The router uses Haiku.
- **Office:** the 🏢 Office button shows the team as pixel-art characters in an office (`static/office.js`, original art drawn in code). Working agents sit at their desks and type; idle ones wander to the lounge. New messages pop up as speech bubbles, and clicking someone opens their DM.
- **Scripts:** `python post.py <channel> <author> "text"` posts a message, for example from scheduled standups.

## Run on the VM
- Config in `/home/turichips/.turichips.env` (never committed): `CLAUDE_CODE_OAUTH_TOKEN=…`, `MAX_PARALLEL_AGENTS=4`
- `sudo systemctl enable --now turichips-chat`, logs with `journalctl -u turichips-chat -f`
- The app listens on `127.0.0.1:8600` only. Open it through an SSH tunnel:
  `ssh -N -L 8600:localhost:8600 <vm>`, then go to http://localhost:8600
