# Discord bot

One bot that lets the manager talk to every agent from Discord.

- **Agent channels** (`#vera`, `#rook`, …): your message starts a thread, and that agent replies in it.
- **`#general`:** name an agent ("rook, can you…") and it replies. Name several and each gets its own thread. Name nobody and Vera answers.
- **Threads:** one thread = one Claude Code session. Reply in the thread to continue.
- **Workspaces:** each agent works in its own git worktree at `~/work/<name>` on branch `agent/<name>`. Company docs are always read fresh from `origin/main`.
- **Access:** only Discord user IDs in `ALLOWED_USER_IDS` can trigger agents.

## Config: `/home/turichips/.turichips.env` (never committed)
```
DISCORD_TOKEN=...
ALLOWED_USER_IDS=...
CLAUDE_CODE_OAUTH_TOKEN=...   # from `claude setup-token`
MAX_PARALLEL_AGENTS=2
```

## Run
`sudo systemctl enable --now turichips-bot`, then logs with `journalctl -u turichips-bot -f`.
