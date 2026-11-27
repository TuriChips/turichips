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
    {"id": "work", "topic": "Shift log: one line per finished piece of work. /status, /pause, /resume work in any channel."},
    {"id": "needs-sai", "topic": "Waiting on Sai: sai-review PRs, decisions, access. Plus a daily list of sai-review PRs."},
]

# Dispatcher (dispatcher.py): GitHub becomes tasks on a board; each ready task goes to its owner's persona,
# with a model picked by task kind and a seat picked by headroom. See checkpoint.md for the design.
DISPATCH = {
    "enabled": os.environ.get("SHIFT_ENABLED", "1") == "1",   # SHIFT_ENABLED=0 turns the dispatcher off
    "org": "TuriChips",              # every repo in this org is scanned for issues and PRs
    "poll_seconds": 120,             # how often GitHub is read; any change dispatches at once
    "tick_seconds": 5 * 60,          # dispatch at least this often even when nothing changed
    "continue_gap_seconds": 5 * 60,  # an issue task that ended DONE continues after this
    "planner_gap_seconds": 60 * 60,  # the planner (Igris) runs at most this often
    # Supervisor (dispatcher.py, "Company state"): when nothing is running or ready, one Haiku call decides
    # whether work can move, the queue needs planning, or everything is waiting on Sai.
    "quiet_grace_seconds": 10 * 60,  # nothing running or ready for this long: the team is quiet, check why
    "check_min_seconds": 15 * 60,    # gap after a check that led nowhere; doubles each time...
    "check_max_seconds": 4 * 3600,   # ...up to this. Any DONE resets it.
    "max_nudges": 2,                 # the supervisor may wake one task this often in a row without a DONE
    "planner_idle_limit": 2,         # planner turns in a row that filed nothing: stop planning, tell Sai
    "stall_seconds": 20 * 60,        # no output from a running turn for this long: warn in #needs-sai (never kill)
    "task_timeout_seconds": 6 * 3600,  # safety net only; long-horizon turns are the point
    "sai_digest_hour_ist": 10,       # daily list of open sai-review PRs in #needs-sai, first poll after this hour
}

# Seats: a shared pool, not one seat per agent. Any persona runs on any pool seat; the budget watcher
# (seats.py) picks the seat with the most room against its weekly pace and keeps a buffer on every seat.
# The seats are split with TuriMath (same accounts, same VM): seat1 is TuriChips' own, seat2 TuriMath's own,
# seat0 (Sai's, CLAUDE_CODE_OAUTH_TOKEN) and seat3 are shared by both. Each factory sees the shared seats' real
# usage (it comes back with every run), so neither plans on room the other has taken.
POOL = ["seat0", "seat1", "seat3"]
WEEKLY_BUFFER = 0.08                 # never plan to use the last 8% of a seat's week
FIVE_HOUR_CEILING = 0.95             # no new launches on a seat past this in its 5-hour window
SEAT_MAX_RUNNING = 2                 # turns at once per seat (task + chat)
MACHINE_MAX_RUNNING = int(os.environ.get("FACTORY_MACHINE_MAX_RUNNING", "3"))   # turns at once on the whole VM:
                                     # no new task turns past this; chat with Sai still runs. 3 suits the old 2 vCPU / 8 GB
                                     # VM (on 2026-11-24 six turns at once, P&R + zexdoc, froze it). Since 2026-11-27 the VM
                                     # is 8 vCPU / 32 GB and the env file sets 6.
AHEAD_OF_PACE = 0.10                 # every seat this far ahead of weekly pace: only urgent work goes out
CHAT_FALLBACK_SEAT = "seat0"         # chat with Sai still works when the whole pool is out

# Models are picked per task kind, not per agent.
MODELS = {"opus": "claude-opus-5-5", "sonnet": "claude-sonnet-5-5", "haiku": "claude-haiku-5-5"}
TASK_KINDS = {   # priority: lower goes first. urgent: still dispatched when every seat is ahead of pace.
    "fix-ci":      {"priority": 1, "model": "sonnet", "urgent": True,  "label": "Fix failing CI"},
    "conflict":    {"priority": 2, "model": "sonnet", "urgent": True,  "label": "Resolve merge conflict"},
    "review":      {"priority": 3, "model": "sonnet", "urgent": True,  "label": "Review PR"},
    "break":       {"priority": 3, "model": "opus",   "urgent": True,  "label": "Break PR (adversarial review)"},
    "pr-followup": {"priority": 4, "model": "sonnet", "urgent": False, "label": "Follow up on your PR"},
    "implement":   {"priority": 5, "model": "sonnet", "urgent": False, "label": "Work on issue"},
    "spec":        {"priority": 5, "model": "opus",   "urgent": False, "label": "Spec work"},
    "plan":        {"priority": 6, "model": "opus",   "urgent": False, "label": "Plan the queue"},
    "chat":        {"priority": 0, "model": "sonnet", "urgent": True,  "label": "Chat"},
}
REVIEW_KIND = {"beru": "break"}      # reviewer -> kind (Beru's reviews are adversarial, on Opus)
ISSUE_KIND = {"igris": "spec"}       # owner -> kind for their issues (Igris's issues are spec work, on Opus)
PLANNER = "igris"

# Posts from the scheduler itself (command replies) use this author.
SYSTEM = {"id": "shift", "name": "Shift", "role": "Scheduler", "color": "#475569"}

# Seats outside the pool that the Usage tab still tracks, with the label shown in place of agent names.
USAGE_ONLY_SEATS = {"seat2": "TuriMath's seat", "seat4": "shared outside the company, no agents"}

# The personas. Every agent also gets a direct-message channel: dm-<id>.
# Seat tokens are CLAUDE_TOKEN_<SEAT> in the env file (a seat without one falls back to CLAUDE_CODE_OAUTH_TOKEN).
AGENTS = {
    "igris":  {"name": "Igris",  "file": "architect",       "role": "Architect",                         "color": "#7c3aed"},
    "zura":  {"name": "Zura",  "file": "designer-a",      "role": "Designer A (control)",              "color": "#2563eb"},
    "ada":  {"name": "Ada",  "file": "designer-b",      "role": "Designer B (data)",                 "color": "#0891b2"},
    "titus": {"name": "Titus", "file": "verification-a",  "role": "Verification A (test builder)",     "color": "#059669"},
    "beru":  {"name": "Beru",  "file": "verification-b",  "role": "Verification B (breaker)",          "color": "#dc2626"},
    "tesla":  {"name": "Tesla",  "file": "infrastructure",  "role": "Infrastructure",                    "color": "#64748b"},
    "leo": {"name": "Leo", "file": "physical-design", "role": "Physical Design",                   "color": "#d97706"},
    "homer":  {"name": "Homer",  "file": "software-docs",   "role": "Software and Docs",                 "color": "#db2777"},
}

ROUTER_DEFAULT = "igris"

# A DM or channel conversation starts a fresh Claude session after this much silence.
DM_IDLE_RESET_SECONDS = 4 * 3600
