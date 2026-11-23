# Checkpoint: harness redesign (2026-11-23)

## Why we're redesigning

Seat2 (Ada, Beru, Homer) hit its weekly limit on **Sun 22 Nov ~23:30 IST** (resets Tue 24 Nov 09:30 IST). Most of that usage was agents replying "IDLE".

**Root cause:** `session_reset_seconds` (12 h) is measured from the *last* turn (`db.session()`), and the shift scheduler wakes every agent roughly every 30 min. So the reset never fires, and every agent has run in one session since 14 Nov (trace files: Ada 17 MB, Beru 35 MB, Homer 43 MB). Each wake reloaded about 500–600K tokens of context into a cold cache (5-min TTL) to produce a one-word reply.

- From 19 to 22 Nov, 86 of Beru's 100 shift turns and 88 of Homer's 99 were IDLE.
- Seat2 output was about 7–20K tokens a day; cache writes were 35–43M tokens a day.
- Seat1 and seat3 show the same pattern and are heading the same way.
- The cost figures on the Usage tab are wrong (they look like whole-session totals counted again on every turn).

Stopgap not yet done: clearing the `work:*` rows in the `sessions` table so agents start fresh.

## The shift: stop waking agents and start dispatching tasks

Today the agent is the unit of work. Make the **task** the unit, and treat the agent as a role that gets attached to a task.

```
GitHub / chat / CI ──► Company Log (append-only: everything that happened)
                              │
                              ▼
                       Task Board (what's pending, derived from the log)
                              │
                 Dispatcher (every 5 min + on events)
                 picks: task → role → model → seat
                              │
                              ▼
              claude -p  with that task's context pack + its own session
                              │
                              └──► writes results + handoff back into the log
```

Four separate things that are currently all mixed into "agent":
- **Task:** what needs doing. It has a type, a priority, dependencies and its own session.
- **Role:** who does it (Igris, Beru…). This means the persona, what they own and their judgment, but not the model or the seat.
- **Model:** chosen by task type.
- **Seat:** just capacity, picked when the task launches.

## 1. Route the model by task type

| Task type | Model | Notes |
|---|---|---|
| Merge an approved, green PR | **no LLM** | `gh pr merge` is deterministic. Today Igris spends Opus on it. |
| Triage / route / status reply | Haiku | |
| Review a PR | Sonnet | |
| Implement / fix CI / write docs | Sonnet | |
| Adversarial break (Beru) | Opus | |
| Spec, architecture, hard debug | Opus | |
| Escalation | Opus | When a Sonnet task fails twice on the same thing |

Plenty of what currently goes to an LLM doesn't need one. The dispatcher should handle the mechanical work itself.

## 2. A context pack for each task type

Each launch is built from four layers:
- **Role file:** who you are. This exists already.
- **Playbook for the task type:** how to do this kind of task, e.g. a review checklist or a CI-fix procedure.
- **Task brief:** what to do. Issue body, PR diff, CI log excerpt, plus the last handoff note on this task.
- **Log slice:** only the recent company-log entries that touch this task's repo or issue.

Tools also follow the task type, set with `--allowedTools`:
- A review gets read access and `gh pr comment` only, with no push.
- An implement task gets everything.

Each task also runs in its own git worktree. That keeps the context small and limits what a wrong turn can damage.

## 3. Seats as a pool, plus a budget watcher

All of the seats are Team seats with the same capabilities, so any role can run on any seat. When a task launches, the dispatcher scores each seat by headroom:
- **Weekly pacing:** remaining weekly budget compared with time left until the reset. A seat behind schedule is "cheap" to use; one ahead of schedule is "expensive".
- **5-hour window:** how much is left in the current 5-hour block.
- **Blocked:** a blocked seat is skipped until it resets.

Several roles can share a seat at once. Two rules:
- **Sticky while a task is active.** A task's session stays on the seat it started on, because the prompt cache is most likely per account and moving would mean paying to rebuild it. Rebalancing happens between tasks.
- **The watcher only stops *new* launches.** It never kills running work.

## 4. A smart timer driven by the company log

Every 5 minutes, plus straight away on events:
1. Pull new events (GitHub, chat, CI) into the log.
2. Rules update the board. For example, a `review:beru` label creates a review task, a red CI run creates a fix-CI task, and approved + green leads to the dispatcher merging it itself.
3. Dispatch tasks that are ready: dependencies met, the role is free and the budget allows it.
4. **Bring in an LLM planner (Igris, on Opus) only when the rules can't decide.** That means the board is empty but the roadmap has work, a task has stalled, or an issue has no owner.

No LLM reads the log every 5 minutes; that would just move the "IDLE" burn somewhere else. The rules decide in most cases, and the planner handles the exceptions, maybe at most once an hour.

**The log versus the board:**
- **The log** is append-only and is the company's memory: every event, decision, turn result and handoff.
- **The board** is current state worked out from the log.

Agents read only their slice of the log, and they write handoffs and decisions back into it.

## 5. No cap on turns, but stall detection

No turn cap; agents are meant to run long-horizon. Instead, watch for real problems:
- No new commits or tool progress for N minutes.
- The same failing command repeated over and over.
- A session's context getting close to its limit.

Any of these gets flagged in #needs-sai; nothing is killed automatically. Inside a long task, Claude Code's own context compaction handles growth.

## 6. Session lifecycle per task

- **Created:** the task is created, and its first dispatch makes a new session.
- **Follow-ups:** review comments or a red CI run on that task resume the same session.
- **Done:** the task closes and the session is archived.

Every turn ends with a handoff note in the log. If a session gets too big or goes bad, a fresh one can start from that note without losing anything.

## Decisions (Sai, 2026-11-23)

1. **Seat pool:** seat1, seat2 and seat3. seat0 may join from next week. seat4 stays out (shared with a friend).
2. **Weekly pacing:** keep a 5–10% buffer on every seat's weekly limit.
3. **Company log:** SQLite on the VM.
4. **Roles:** keep the fixed personas. An agent = persona + context + tools + memory; the dispatcher routes each task to the agent that owns it, and picks the model and seat per task.
