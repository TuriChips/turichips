"""Workspace layout. Channels are added here in code, not from the UI."""

WORKSPACE = "TuriChips"
MANAGER = {"id": "sai", "name": "Sai", "role": "Manager", "color": "#1d9bd1"}

# Shared channels. Agents reply inline, like a group chat; in a thread only when Sai replies in one.
# @name pulls in one agent, @all (or @everyone/@channel/@here/@team) pulls in everyone,
# and with no tag a fast model picks who should answer (ROUTER_DEFAULT if unsure).
CHANNELS = [
    {"id": "general", "topic": "Company-wide. Tag @name or @all, or just talk and the right people answer."},
    {"id": "standup", "topic": "Standups: Passed / In progress / Blocked."},
    {"id": "reviews", "topic": "Weekly reviews: what shipped, what slipped, what to do better."},
]

# Every agent also gets a direct-message channel: dm-<id>.
# model: pinned so a change in Claude Code's default never silently changes an agent.
# Opus for Vera (spec errors spread to everyone) and Rook (subtle bugs); Sonnet for the rest.
# account: which Claude Team seat the agent runs on. Its token is CLAUDE_TOKEN_<ACCOUNT> in the env file
# (falls back to CLAUDE_CODE_OAUTH_TOKEN). Opus agents and heavy builders are spread across seats.
AGENTS = {
    "vera":  {"name": "Vera",  "file": "architect",       "role": "Architect",                         "model": "claude-opus-5-5", "account": "seat1", "color": "#7c3aed"},
    "theo":  {"name": "Theo",  "file": "designer-a",      "role": "Designer A (control)",              "model": "claude-sonnet-5-5", "account": "seat3", "color": "#2563eb"},
    "mira":  {"name": "Mira",  "file": "designer-b",      "role": "Designer B (data)",                 "model": "claude-sonnet-5-5", "account": "seat4", "color": "#0891b2"},
    "quinn": {"name": "Quinn", "file": "verification-a",  "role": "Verification A (test builder)",     "model": "claude-sonnet-5-5", "account": "seat4", "color": "#059669"},
    "rook":  {"name": "Rook",  "file": "verification-b",  "role": "Verification B (breaker)",          "model": "claude-opus-5-5", "account": "seat2", "color": "#dc2626"},
    "otto":  {"name": "Otto",  "file": "infrastructure",  "role": "Infrastructure",                    "model": "claude-sonnet-5-5", "account": "seat1", "color": "#64748b"},
    "petra": {"name": "Petra", "file": "physical-design", "role": "Physical Design",                   "model": "claude-sonnet-5-5", "account": "seat3", "color": "#d97706"},
    "juno":  {"name": "Juno",  "file": "software-docs",   "role": "Software and Docs",                 "model": "claude-sonnet-5-5", "account": "seat2", "color": "#db2777"},
}

ROUTER_DEFAULT = "vera"

# A DM or channel conversation starts a fresh Claude session after this much silence.
DM_IDLE_RESET_SECONDS = 4 * 3600
