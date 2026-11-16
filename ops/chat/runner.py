"""Runs one agent turn with Claude Code, inside that agent's own git worktree."""
import asyncio
import json
import os
import subprocess
from pathlib import Path

from config import AGENTS
from gate import wait_turn
import usage

REPO = Path(os.environ.get("TURICHIPS_REPO", Path.home() / "turichips"))
WORK = Path(os.environ.get("TURICHIPS_WORK", Path.home() / "work"))
CLAUDE = os.environ.get("CLAUDE_BIN", str(Path.home() / ".local/bin/claude"))
TIMEOUT = int(os.environ.get("AGENT_TIMEOUT_SECONDS", "1800"))

_git_lock = asyncio.Lock()


def _git(*args, cwd=REPO):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def _show(path: str) -> str:
    """A file as it is on origin/main, so every agent sees the latest company docs."""
    r = _git("show", f"origin/main:{path}")
    return r.stdout if r.returncode == 0 else ""


def _prepare_sync(agent: str) -> tuple[Path, str]:
    """Blocking git work. Always called in a worker thread so the server never freezes."""
    _git("fetch", "-q", "origin")
    wt = WORK / agent
    if not wt.exists():
        WORK.mkdir(parents=True, exist_ok=True)
        branch = f"agent/{agent}"
        if _git("rev-parse", "--verify", branch).returncode != 0:
            _git("branch", branch, "origin/main")
        r = _git("worktree", "add", "-q", str(wt), branch)
        if r.returncode != 0:
            raise RuntimeError(f"could not create worktree for {agent}: {r.stderr.strip()}")
    prompt = "\n\n---\n\n".join([
        _show("COMPANY.md"),
        _show("agents/_rules.md"),
        _show(f"agents/{AGENTS[agent]['file']}.md"),
        (
            "## Where you are\n"
            f"You are talking with Sai, the operator, in the TuriChips chat app (it works like Slack). "
            f"Your working copy is {wt} on branch agent/{agent}. The company docs above are the latest "
            "from origin/main. Keep chat replies short and plain; markdown is rendered. Put real work in "
            "the repo and open pull requests against main by pushing your branch."
        ),
    ])
    return wt, prompt


async def prepare(agent: str) -> tuple[Path, str]:
    async with _git_lock:
        return await asyncio.to_thread(_prepare_sync, agent)


def account_env(agent: str) -> dict:
    """Environment for one agent's Claude run, logged in as that agent's Team seat."""
    return seat_env(AGENTS[agent].get("account", ""))


def seat_env(seat: str) -> dict:
    env = os.environ.copy()
    token = os.environ.get(f"CLAUDE_TOKEN_{seat.upper()}") if seat else None
    if token:
        env["CLAUDE_CODE_OAUTH_TOKEN"] = token
    for k in [k for k in env if k.startswith("CLAUDE_TOKEN_")]:
        del env[k]                       # an agent never sees other seats' tokens
    return env


async def run_turn(agent: str, message: str, session_id: str, resume: bool) -> tuple[str, bool]:
    """Returns (reply text, ok). The session only counts as started when ok is True."""
    wt, system_prompt = await prepare(agent)
    cmd = [CLAUDE, "-p", message, "--output-format", "stream-json", "--verbose", "--model", AGENTS[agent]["model"],
           "--append-system-prompt", system_prompt,
           "--dangerously-skip-permissions"]  # runs as the isolated `turichips` user
    cmd += ["--resume", session_id] if resume else ["--session-id", session_id]
    await wait_turn()
    proc = await asyncio.create_subprocess_exec(
        *cmd, cwd=wt, env=account_env(agent), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=TIMEOUT)
    except asyncio.TimeoutError:
        proc.kill()
        return f"I ran out of time ({TIMEOUT // 60} min) on this one. Reply to let me continue.", resume
    data, rate = parse_stream(out)
    try:
        usage.record(AGENTS[agent].get("account", ""), rate, data)
    except Exception as e:               # usage numbers must never cost a reply
        print(f"usage record failed: {e}", flush=True)
    if data is not None:
        return data.get("result") or "(no reply)", not data.get("is_error", False)
    tail = (err or out).decode(errors="replace")[-800:] or "(no output)"
    return f"Something broke while I was working (exit code {proc.returncode}):\n```\n{tail}\n```", False


def parse_stream(out: bytes) -> tuple[dict | None, dict | None]:
    """(final result event, last rate_limit_info) from Claude Code's stream-json output."""
    result = rate = None
    for line in out.decode(errors="replace").splitlines():
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "result":
            result = ev
        elif ev.get("type") == "rate_limit_event":
            rate = ev.get("rate_limit_info") or rate
    return result, rate
