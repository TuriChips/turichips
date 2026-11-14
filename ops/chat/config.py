"""Workspace layout. Channels are added here in code, not from the UI."""
import os

WORKSPACE = "TuriChips"
MANAGER = {"id": "sai", "name": "Sai", "role": "Operator", "color": "#1d9bd1"}

# Shared channels. Agents reply inline, like a group chat; in a thread only when Sai replies in one.
# @name pulls in one agent, @all (or @everyone/@channel/@here/@team) pulls in everyone,
# and with no tag a fast model picks who should answer (ROUTER_DEFAULT if unsure).
CHANNELS = [
    {"id": "general", "topic": "Company-wide. Tag @name or @all, or just talk and the right people answer."},
    {"id": "standup", "topic": "Standups: Passed / In progress / Blocked."},
    {"id": "reviews", "topic": "Weekly reviews: what shipped, what slipped, what to do better."},
    {"id": "work", "topic": "Shift log: one line per work turn. /status, /pause, /resume work in any channel."},
]

# Shifts (shift.py): agents keep working from GitHub without being messaged.
SHIFT = {
    "enabled": os.environ.get("SHIFT_ENABLED", "1") == "1",   # SHIFT_ENABLED=0 turns the scheduler off
    "org": "TuriChips",              # every repo in this org is scanned for issues and PRs
    "merger": "igris",                # merges approved, green PRs and keeps the queue full
    "poll_seconds": 120,             # how often GitHub is read
    "work_gap_seconds": 5 * 60,      # after a DONE turn, while the agent still has open items
    "blocked_gap_seconds": 30 * 60,  # after BLOCKED
    "idle_gap_seconds": 60 * 60,     # after IDLE, or when nothing is assigned
    "max_parallel": 3,               # work turns at once; leaves room in MAX_PARALLEL_AGENTS for Sai's chat
    "session_reset_seconds": 12 * 3600,
}

# Posts from the scheduler itself (command replies) use this author.
SYSTEM = {"id": "shift", "name": "Shift", "role": "Scheduler", "color": "#475569"}

# Every agent also gets a direct-message channel: dm-<id>.
# model: pinned so a change in Claude Code's default never silently changes an agent.
# Opus for Igris (spec errors spread to everyone) and Beru (subtle bugs); Sonnet for the rest.
# account: which Claude Team seat the agent runs on. Its token is CLAUDE_TOKEN_<ACCOUNT> in the env file
# (falls back to CLAUDE_CODE_OAUTH_TOKEN). Opus agents and heavy builders are spread across seats.
AGENTS = {
    "igris":  {"name": "Igris",  "file": "architect",       "role": "Architect",                         "model": "claude-opus-5-5", "account": "seat1", "color": "#7c3aed"},
    "zura":  {"name": "Zura",  "file": "designer-a",      "role": "Designer A (control)",              "model": "claude-sonnet-5-5", "account": "seat3", "color": "#2563eb"},
    "ada":  {"name": "Ada",  "file": "designer-b",      "role": "Designer B (data)",                 "model": "claude-sonnet-5-5", "account": "seat4", "color": "#0891b2"},
    "titus": {"name": "Titus", "file": "verification-a",  "role": "Verification A (test builder)",     "model": "claude-sonnet-5-5", "account": "seat4", "color": "#059669"},
    "beru":  {"name": "Beru",  "file": "verification-b",  "role": "Verification B (breaker)",          "model": "claude-opus-5-5", "account": "seat2", "color": "#dc2626"},
    "tesla":  {"name": "Tesla",  "file": "infrastructure",  "role": "Infrastructure",                    "model": "claude-sonnet-5-5", "account": "seat1", "color": "#64748b"},
    "leo": {"name": "Leo", "file": "physical-design", "role": "Physical Design",                   "model": "claude-sonnet-5-5", "account": "seat3", "color": "#d97706"},
    "homer":  {"name": "Homer",  "file": "software-docs",   "role": "Software and Docs",                 "model": "claude-sonnet-5-5", "account": "seat2", "color": "#db2777"},
}

ROUTER_DEFAULT = "igris"

# A DM or channel conversation starts a fresh Claude session after this much silence.
DM_IDLE_RESET_SECONDS = 4 * 3600
