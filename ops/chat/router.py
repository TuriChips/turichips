"""Decides which agents answer an untagged channel message, using a fast, cheap model."""
import asyncio
import json
import os
import re

from config import AGENTS, ROUTER_DEFAULT

CLAUDE = os.environ.get("CLAUDE_BIN", os.path.expanduser("~/.local/bin/claude"))
MODEL = os.environ.get("ROUTER_MODEL", "haiku")
ALL_TAGS = re.compile(r"@(all|everyone|channel|here|team)\b", re.I)


def tagged(text: str) -> list[str]:
    if ALL_TAGS.search(text):
        return list(AGENTS)
    return [a for a in AGENTS if re.search(rf"@{a}\b", text, re.I)]


async def pick(channel: str, text: str, context: str = "") -> list[str]:
    roster = "\n".join(f"- {a}: {v['name']}, {v['role']}" for a, v in AGENTS.items())
    prompt = (
        f"You route messages in the #{channel} channel of Turichips, a chip design lab staffed by AI agents.\n"
        f"Team:\n{roster}\n\n"
        + (f"Thread so far:\n{context}\n\n" if context else "")
        + f"The manager, Sai, wrote:\n{text}\n\n"
        "Who should reply? Greetings or messages addressed to everyone or the team: all agents. "
        "A question about a specific area: only the agents who own it. If unclear: the architect.\n"
        'Answer with JSON only, like {"agents": ["vera", "rook"]}.'
    )
    proc = await asyncio.create_subprocess_exec(
        CLAUDE, "-p", prompt, "--model", MODEL, "--output-format", "json", "--max-turns", "1",
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL, cwd="/tmp")
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
        result = json.loads(out).get("result", "")
        names = json.loads(re.search(r"\{.*\}", result, re.S).group(0)).get("agents", [])
        picked = [a for a in AGENTS if a in {str(n).lower() for n in names}]
        return picked or [ROUTER_DEFAULT]
    except Exception:
        if proc.returncode is None:
            proc.kill()
        return [ROUTER_DEFAULT]
