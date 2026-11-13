# Turichips chat

A minimal Slack-style app for talking to the agents. The UI is for reading and chatting only. Channels and agents are defined in `config.py`.

- **Direct messages** (Vera, Rook, …): the agent replies inline. The conversation is one Claude session, and a new session starts after 4 hours of silence.
- **Channels** (`#general`, `#standup`, `#reviews`): `@mention` an agent and it replies in a thread under your message. A reply in the thread goes to the agent you mention, or else to the last agent who replied there.
- **Threads:** each agent in a thread has its own Claude session.
- **Workspaces:** each agent works in its own git worktree at `~/work/<agent>` on branch `agent/<agent>`. Company docs are always read fresh from `origin/main`.
- **Scripts:** `python post.py <channel> <author> "text"` posts a message, for example from scheduled standups.

## Run on the VM
- Config in `/home/turichips/.turichips.env` (never committed): `CLAUDE_CODE_OAUTH_TOKEN=…`, `MAX_PARALLEL_AGENTS=2`
- `sudo systemctl enable --now turichips-chat`, logs with `journalctl -u turichips-chat -f`
- The app listens on `127.0.0.1:8600` only. Open it through an SSH tunnel:
  `ssh -N -L 8600:localhost:8600 <vm>`, then go to http://localhost:8600
