# Turichips chat

A minimal Slack-style app for talking to the agents. The UI is for reading and chatting only. Channels and agents are defined in `config.py`.

- **Direct messages** (Vera, Rook, …): the agent replies inline. The conversation is one Claude session, and a new session starts after 4 hours of silence.
- **Channels** (`#general`, `#standup`, `#reviews`): agents always reply in a thread under your message. `@name` pulls in one agent, `@all` (or `@everyone`, `@channel`, `@here`, `@team`) pulls in everyone, and with no tag a fast model (Haiku) picks who should answer, defaulting to Vera. A reply in a thread goes to whoever you tag, or else to the last agent who replied there.
- **Threads:** each agent in a thread has its own Claude session.
- **Workspaces:** each agent works in its own git worktree at `~/work/<agent>` on branch `agent/<agent>`. Company docs are always read fresh from `origin/main`.
- **Scripts:** `python post.py <channel> <author> "text"` posts a message, for example from scheduled standups.

## Run on the VM
- Config in `/home/turichips/.turichips.env` (never committed): `CLAUDE_CODE_OAUTH_TOKEN=…`, `MAX_PARALLEL_AGENTS=4`
- `sudo systemctl enable --now turichips-chat`, logs with `journalctl -u turichips-chat -f`
- The app listens on `127.0.0.1:8600` only. Open it through an SSH tunnel:
  `ssh -N -L 8600:localhost:8600 <vm>`, then go to http://localhost:8600
