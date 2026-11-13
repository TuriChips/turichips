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
- Vera merges PRs labelled "approved" with green CI, unless they carry "sai-review" (those wait for Sai).

Each work turn's report is posted to #work. Sai controls shifts with /pause, /resume and /status.
"""
import asyncio
import json
import re
import subprocess
import time
import uuid

import db
from config import AGENTS, SHIFT
from runner import run_turn

ORG = SHIFT["org"]
MERGER = SHIFT["merger"]
NAME_TO_ID = {v["name"].lower(): k for k, v in AGENTS.items()}

state = {a: {"next": 0.0, "last_result": "", "last_end": 0.0, "fp": None, "rebase": False, "items": []}
         for a in AGENTS}
_ctx = {}


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
            if "approved" in labels and "sai-review" not in labels and ci in ("green", "none"):
                items[MERGER].append({"kind": "merge", "ref": ref, "title": p["title"], "ci": ci,
                                      "updated": p["updatedAt"]})
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
        "DONE: <what you did, with PR/issue refs>  or  BLOCKED: <what, and who can unblock>  or  IDLE: <why>"
    )


def _result_kind(text: str) -> str:
    last = text.strip().splitlines()[-1] if text.strip() else ""
    m = re.match(r"\W*(DONE|BLOCKED|IDLE)\b", last, re.I)
    return m.group(1).upper() if m else "DONE"


def _report(text: str) -> str:
    """Short report for #work: the status line, or the tail of the reply if the agent didn't give one."""
    lines = [l for l in text.strip().splitlines() if l.strip()]
    if lines and re.match(r"\W*(DONE|BLOCKED|IDLE)\b", lines[-1], re.I):
        return lines[-1].strip().strip("*")
    return text.strip()[-600:]


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
                answer, ok = f"BLOCKED: shift turn crashed: `{e}`", False
            finally:
                working.pop(agent, None)
        if ok:
            db.save_session(key, session)
    kind = _result_kind(answer) if ok else "BLOCKED"
    gap = {"DONE": SHIFT["work_gap_seconds"], "BLOCKED": SHIFT["blocked_gap_seconds"],
           "IDLE": SHIFT["idle_gap_seconds"]}[kind]
    if kind == "DONE" and not items:
        gap = SHIFT["idle_gap_seconds"]
    s = state[agent]
    s.update(last_result=kind, last_end=time.time(), next=time.time() + gap, rebase=True)
    db.add("work", agent, _report(answer) if ok else answer[-600:])


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
