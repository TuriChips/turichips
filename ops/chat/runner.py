"""Runs one agent turn with Claude Code, inside that agent's own git worktree."""
import asyncio
import json
import os
import subprocess
from pathlib import Path

from config import AGENTS
from gate import wait_turn

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
            f"You are talking with Sai, the manager, in the TuriChips chat app (it works like Slack). "
            f"Your working copy is {wt} on branch agent/{agent}. The company docs above are the latest "
            "from origin/main. Keep chat replies short and plain; markdown is rendered. Put real work in "
            "the repo and open pull requests against main by pushing your branch."
        ),
    ])
    return wt, prompt


async def prepare(agent: str) -> tuple[Path, str]:
    async with _git_lock:
        return await asyncio.to_thread(_prepare_sync, agent)


async def run_turn(agent: str, message: str, session_id: str, resume: bool) -> tuple[str, bool]:
    """Returns (reply text, ok). The session only counts as started when ok is True."""
    wt, system_prompt = await prepare(agent)
    cmd = [CLAUDE, "-p", message, "--output-format", "json", "--model", AGENTS[agent]["model"],
           "--append-system-prompt", system_prompt,
           "--dangerously-skip-permissions"]  # runs as the isolated `turichips` user
    cmd += ["--resume", session_id] if resume else ["--session-id", session_id]
    await wait_turn()
    proc = await asyncio.create_subprocess_exec(
        *cmd, cwd=wt, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=TIMEOUT)
    except asyncio.TimeoutError:
        proc.kill()
        return f"I ran out of time ({TIMEOUT // 60} min) on this one. Reply to let me continue.", resume
    try:
        data = json.loads(out)
        return data.get("result") or "(no reply)", not data.get("is_error", False)
    except json.JSONDecodeError:
        tail = (err or out).decode(errors="replace")[-800:] or "(no output)"
        return f"Something broke while I was working (exit code {proc.returncode}):\n```\n{tail}\n```", False
