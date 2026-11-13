"""Runs one agent turn with Claude Code, inside that agent's own git worktree."""
import asyncio
import json
import os
import subprocess
from pathlib import Path

REPO = Path(os.environ.get("TURICHIPS_REPO", Path.home() / "turichips"))
WORK = Path(os.environ.get("TURICHIPS_WORK", Path.home() / "work"))
CLAUDE = os.environ.get("CLAUDE_BIN", str(Path.home() / ".local/bin/claude"))
TIMEOUT = int(os.environ.get("AGENT_TIMEOUT_SECONDS", "1800"))

_git_lock = asyncio.Lock()


def _git(*args, cwd=REPO):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def _show(path: str) -> str:
    """Read a file as it is on origin/main, so every agent sees the latest company docs."""
    r = _git("show", f"origin/main:{path}")
    return r.stdout if r.returncode == 0 else ""


async def prepare(name: str) -> tuple[Path, str]:
    """Fetch, make sure the agent has a worktree, and build its system prompt."""
    async with _git_lock:
        _git("fetch", "-q", "origin")
        wt = WORK / name
        if not wt.exists():
            WORK.mkdir(parents=True, exist_ok=True)
            branch = f"agent/{name}"
            if _git("rev-parse", "--verify", branch).returncode != 0:
                _git("branch", branch, "origin/main")
            _git("worktree", "add", "-q", str(wt), branch)
        from agents import AGENTS
        prompt = "\n\n---\n\n".join([
            _show("COMPANY.md"),
            _show("agents/_rules.md"),
            _show(f"agents/{AGENTS[name]}.md"),
            (
                "## Where you are\n"
                f"You are talking with Sai, the manager, on Discord. Your working copy is {wt} "
                f"on branch agent/{name}. Company docs above are the latest from origin/main. "
                "Keep Discord replies short and plain. Put real work in the repo and open pull requests "
                "against main with `gh` or by pushing your branch."
            ),
        ])
    return wt, prompt


async def run_turn(name: str, message: str, session_id: str, resume: bool) -> str:
    wt, system_prompt = await prepare(name)
    cmd = [
        CLAUDE, "-p", message,
        "--output-format", "json",
        "--append-system-prompt", system_prompt,
        "--dangerously-skip-permissions",  # runs as the isolated `turichips` user
    ]
    cmd += ["--resume", session_id] if resume else ["--session-id", session_id]
    proc = await asyncio.create_subprocess_exec(
        *cmd, cwd=wt, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=TIMEOUT)
    except asyncio.TimeoutError:
        proc.kill()
        return f"I ran out of time ({TIMEOUT // 60} min) on this one. Reply here to let me continue."
    try:
        data = json.loads(out)
        return data.get("result") or "(no reply)"
    except json.JSONDecodeError:
        tail = (err or out).decode(errors="replace")[-800:]
        return f"Something broke while I was working:\n```\n{tail}\n```"
