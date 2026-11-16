"""Shifts: keeps agents working without anyone messaging them.

Every POLL_SECONDS the scheduler reads the open issues and pull requests in every repo of the GitHub org,
works out what each agent has on its plate, and wakes agents for a work turn:
- right away when something of theirs changed (new issue, review request, failing CI, merge-ready PR),
- after WORK_GAP when the last turn ended DONE and they still have open items,
- after IDLE_GAP when they reported IDLE or have nothing; after BLOCKED_GAP when they reported BLOCKED.

Ownership on GitHub (all agents share one GitHub account, so names live in titles, branches and labels):
- issue owner: title starts with "<Name>:" or label "agent:<id>"
- PR author: head branch "agent/<id>" or "<id>/..."
- PR reviewer: label "review:<id>"
- Igris merges PRs labelled "approved" with green CI, unless they carry "sai-review" (those wait for Sai).

Reports: #work gets a line only when a turn ends DONE (finished work). A turn that ends BLOCKED-SAI posts
to #needs-sai, and only when that agent's blocker text changed. IDLE, plain BLOCKED (waiting on another
agent, already visible on GitHub) and replies with no status line post nothing. Once a day the scheduler
lists the open "sai-review" PRs in #needs-sai. Sai controls shifts with /pause, /resume and /status.
"""
import asyncio
import json
import re
import subprocess
import time
import uuid
from datetime import datetime, timedelta, timezone

import db
from config import AGENTS, SHIFT, SYSTEM
from runner import run_turn

ORG = SHIFT["org"]
MERGER = SHIFT["merger"]
NAME_TO_ID = {v["name"].lower(): k for k, v in AGENTS.items()}
NEEDS_SAI = "needs-sai"
IST = timezone(timedelta(hours=5, minutes=30))
STATUS_LINE = re.compile(r"\W*(DONE|BLOCKED-SAI|BLOCKED|IDLE)\b", re.I)

state = {a: {"next": 0.0, "last_result": "", "last_end": 0.0, "fp": None, "rebase": False, "items": [],
             "last_sai": ""}
         for a in AGENTS}
_ctx = {}
sai_queue: list[dict] = []   # open PRs labelled sai-review, refreshed by every snapshot


# ---------- GitHub ----------
def _gh(*args) -> list | dict | None:
    r = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout or "null")
    except json.JSONDecodeError:
        return None


def _owner_of_issue(issue) -> str | None:
    for lb in issue.get("labels", []):
        m = re.fullmatch(r"agent:(\w+)", lb["name"])
        if m and m.group(1) in AGENTS:
            return m.group(1)
    m = re.match(r"\s*(\w+)\s*:", issue["title"])
    return NAME_TO_ID.get(m.group(1).lower()) if m else None


def _author_of_pr(pr) -> str | None:
    m = re.match(r"(?:agent/)?(\w+)(?:/|$)", pr["headRefName"])
    return m.group(1) if m and m.group(1) in AGENTS else None


def _ci(pr) -> str:
    checks = pr.get("statusCheckRollup") or []
    if not checks:
        return "none"
    states = {(c.get("conclusion") or c.get("state") or c.get("status") or "").upper() for c in checks}
    if states & {"FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED"}:
        return "failing"
    if states <= {"SUCCESS", "NEUTRAL", "SKIPPED"}:
        return "green"
    return "running"


def snapshot() -> dict[str, list[dict]] | None:
    """Open work per agent across the org. None if GitHub couldn't be read."""
    repos = _gh("repo", "list", ORG, "--no-archived", "--json", "name", "--limit", "100")
    if repos is None:
        return None
    items = {a: [] for a in AGENTS}
    waiting = []
    for repo in repos:
        full = f"{ORG}/{repo['name']}"
        issues = _gh("issue", "list", "-R", full, "--state", "open", "--limit", "100",
                     "--json", "number,title,labels,updatedAt") or []
        for i in issues:
            owner = _owner_of_issue(i)
            if owner:
                items[owner].append({"kind": "issue", "ref": f"{full}#{i['number']}", "title": i["title"],
                                     "updated": i["updatedAt"]})
        prs = _gh("pr", "list", "-R", full, "--state", "open", "--limit", "100",
                  "--json", "number,title,headRefName,labels,updatedAt,statusCheckRollup,mergeable") or []
        for p in prs:
            labels = {lb["name"] for lb in p.get("labels", [])}
            ci, ref = _ci(p), f"{full}#{p['number']}"
            author = _author_of_pr(p)
            if author:
                items[author].append({"kind": "my-pr", "ref": ref, "title": p["title"], "ci": ci,
                                      "conflict": p.get("mergeable") == "CONFLICTING", "updated": p["updatedAt"]})
            for lb in labels:
                m = re.fullmatch(r"review:(\w+)", lb)
                if m and m.group(1) in AGENTS and "approved" not in labels:
                    items[m.group(1)].append({"kind": "review", "ref": ref, "title": p["title"], "ci": ci,
                                              "updated": p["updatedAt"]})
            if "sai-review" in labels:
                waiting.append({"ref": ref, "title": p["title"], "ci": ci})
            if "approved" in labels and "sai-review" not in labels and ci in ("green", "none"):
                items[MERGER].append({"kind": "merge", "ref": ref, "title": p["title"], "ci": ci,
                                      "updated": p["updatedAt"]})
    sai_queue[:] = waiting
    return items


def fingerprint(items: list[dict]) -> str:
    return "|".join(sorted(f"{i['kind']}:{i['ref']}:{i['updated']}:{i.get('ci', '')}" for i in items))


# ---------- Work turns ----------
def _queue_text(items: list[dict]) -> str:
    if not items:
        return "Nothing on GitHub is assigned to you right now."
    labels = {"issue": "Your issue", "my-pr": "Your PR", "review": "Review requested", "merge": "Ready to merge"}
    out = []
    for i in items:
        extra = ""
        if i["kind"] in ("my-pr", "review", "merge"):
            extra = f" (CI {i['ci']}{', merge conflict' if i.get('conflict') else ''})"
        out.append(f"- {labels[i['kind']]}: {i['ref']} {i['title']}{extra}")
    return "\n".join(out)


def work_prompt(agent: str, items: list[dict]) -> str:
    planner = (
        "\nYou also keep the team's queue full: if the current chip has work nobody owns, split it into issues "
        "titled '<Name>: <task>' in the chip repo, and keep the roadmap moving to the next chip when one is done."
        if agent == MERGER else "")
    return (
        "[shift turn] Nobody messaged you: this is a scheduled work turn while Sai is away.\n\n"
        f"Your queue, read from GitHub just now:\n{_queue_text(items)}\n{planner}\n\n"
        "Take the next concrete step on the most important item: write code, run the tests, commit, push, open "
        "or update a PR, review a PR, or file an issue for someone else. Follow the shift rules in agents/_rules.md. "
        "Do real work, not planning notes. Stop when this step is done.\n\n"
        "End your reply with exactly one line in this form, nothing after it:\n"
        "DONE: <what you finished, with PR/issue refs>\n"
        "BLOCKED-SAI: <what you need from Sai, with PR/issue ref>  (only Sai can unblock: sai-review, a decision, access)\n"
        "BLOCKED: <what, and which agent can unblock>\n"
        "IDLE  (nothing finished this turn; this posts nothing)\n"
        "Only DONE is posted to #work, so use it only when something is actually finished."
    )


def _last_line(text: str) -> str:
    lines = [l for l in text.strip().splitlines() if l.strip()]
    return lines[-1].strip() if lines else ""


def _result_kind(text: str) -> str:
    """DONE, BLOCKED-SAI, BLOCKED or IDLE. A reply without a status line counts as IDLE, so it posts nothing."""
    m = STATUS_LINE.match(_last_line(text))
    return m.group(1).upper() if m else "IDLE"


def _report(text: str) -> str:
    """The status line, without markdown bold."""
    return _last_line(text).strip("*").strip()


async def work_turn(agent: str, items: list[dict]):
    working, locks, slots = _ctx["working"], _ctx["locks"], _ctx["slots"]
    async with _ctx["work_slots"], locks[agent]:
        if paused():
            return
        key = f"work:{agent}"
        session = db.session(key, SHIFT["session_reset_seconds"])
        resume = session is not None
        session = session or str(uuid.uuid4())
        async with slots:
            working[agent] = {"channel": "work", "parent_id": None}
            try:
                answer, ok = await run_turn(agent, work_prompt(agent, items), session, resume)
            except Exception as e:
                answer, ok = f"BLOCKED-SAI: shift turn crashed: `{e}`", False
            finally:
                working.pop(agent, None)
        if ok:
            db.save_session(key, session)
    kind = _result_kind(answer) if ok else "BLOCKED-SAI"
    gap = {"DONE": SHIFT["work_gap_seconds"], "BLOCKED": SHIFT["blocked_gap_seconds"],
           "BLOCKED-SAI": SHIFT["blocked_gap_seconds"], "IDLE": SHIFT["idle_gap_seconds"]}[kind]
    if kind == "DONE" and not items:
        gap = SHIFT["idle_gap_seconds"]
    s = state[agent]
    s.update(last_result=kind, last_end=time.time(), next=time.time() + gap, rebase=True)
    report = _report(answer) if ok else answer[-600:]
    if kind == "DONE":
        db.add("work", agent, report)
    elif kind == "BLOCKED-SAI":
        if report != s["last_sai"]:      # the same blocker again is not news
            db.add(NEEDS_SAI, agent, report)
        s["last_sai"] = report
    if kind != "BLOCKED-SAI":
        s["last_sai"] = ""               # unblocked: a later blocker is news again


# ---------- Scheduler ----------
def paused() -> bool:
    return db.kv_get("shift_paused", "0") == "1"


async def loop():
    await asyncio.sleep(10)
    while True:
        try:
            await tick()
        except Exception as e:  # the scheduler must never die
            print(f"shift tick failed: {e}", flush=True)
        await asyncio.sleep(SHIFT["poll_seconds"])


async def tick():
    if paused():
        return
    snap = await asyncio.to_thread(snapshot)
    if snap is None:
        return
    sai_review_digest()
    now = time.time()
    for agent, items in snap.items():
        s = state[agent]
        fp = fingerprint(items)
        changed = s["fp"] is not None and fp != s["fp"] and not s["rebase"]
        s.update(fp=fp, rebase=False, items=items)
        busy = agent in _ctx["working"] or _ctx["locks"][agent].locked()
        if busy:
            continue
        if changed or now >= s["next"]:
            s["next"] = now + 24 * 3600         # placeholder until the turn ends and sets the real gap
            asyncio.create_task(work_turn(agent, items))


def sai_review_digest():
    """Once a day (from SAI_DIGEST_HOUR_IST), list open sai-review PRs in #needs-sai. Nothing if there are none."""
    now = datetime.now(IST)
    today = now.strftime("%Y-%m-%d")
    if now.hour < SHIFT["sai_digest_hour_ist"] or db.kv_get("sai_digest_day", "") == today:
        return
    db.kv_set("sai_digest_day", today)
    if not sai_queue:
        return
    rows = "\n".join(f"- {p['ref']} {p['title']} (CI {p['ci']})" for p in sai_queue)
    n = len(sai_queue)
    db.add(NEEDS_SAI, SYSTEM["id"], f"📋 **{n} PR{'' if n == 1 else 's'} waiting on your review** "
           f"(label `sai-review`):\n{rows}")


def start(working, locks, slots):
    _ctx.update(working=working, locks=locks, slots=slots,
                work_slots=asyncio.Semaphore(SHIFT["max_parallel"]))
    now = time.time()
    for i, a in enumerate(AGENTS):              # stagger first turns so the team doesn't start all at once
        state[a]["next"] = now + 20 + i * 45
    if SHIFT["enabled"]:
        asyncio.create_task(loop())


# ---------- Commands ----------
def _ago(ts):
    if not ts:
        return "never"
    m = int((time.time() - ts) // 60)
    return f"{m} min ago" if m < 120 else f"{m // 60} h ago"


def status_text() -> str:
    head = "⏸️ **Shifts paused.** `/resume` to restart." if paused() else "▶️ **Shifts running.** `/pause` to stop."
    if not SHIFT["enabled"]:
        head = "⛔ **Shifts are switched off on this server** (`SHIFT_ENABLED=0`)."
    rows = []
    for a, v in AGENTS.items():
        s = state[a]
        now = "🟠 working" if a in _ctx.get("working", {}) else "idle"
        nxt = "—" if paused() or now != "idle" else (
            "soon" if s["next"] - time.time() < 60 else f"in {int((s['next'] - time.time()) // 60)} min")
        last = f"{s['last_result'] or '—'} {_ago(s['last_end']) if s['last_end'] else ''}".strip()
        n = len(s["items"])
        rows.append(f"- **{v['name']}** · {now} · {n} item{'' if n == 1 else 's'} · last {last} · next {nxt}")
    return head + "\n\n" + "\n".join(rows)


def command(text: str) -> str | None:
    """Handles /pause, /resume, /status. Returns the reply, or None if text isn't a command."""
    cmd = text.strip().split()[0].lower() if text.strip().startswith("/") else ""
    if cmd == "/pause":
        db.kv_set("shift_paused", "1")
        return "⏸️ Shifts paused. Turns already running will finish. `/resume` to restart."
    if cmd == "/resume":
        db.kv_set("shift_paused", "0")
        for i, a in enumerate(AGENTS):
            state[a]["next"] = time.time() + 10 + i * 20
        return "▶️ Shifts resumed. Agents will start picking up work in the next few minutes."
    if cmd == "/status":
        return status_text()
    return None
