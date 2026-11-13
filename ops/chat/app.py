"""TuriChips chat: a minimal Slack-like app for talking to the agents."""
import asyncio
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import db
from config import AGENTS, CHANNELS, DM_IDLE_RESET_SECONDS, MANAGER, SYSTEM, WORKSPACE
from router import pick, tagged
from runner import run_turn
import shift
import os

HERE = Path(__file__).parent
MAX_PARALLEL = int(os.environ.get("MAX_PARALLEL_AGENTS", "2"))

app = FastAPI()
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
db.init()

slots = asyncio.Semaphore(MAX_PARALLEL)
agent_locks = {a: asyncio.Lock() for a in AGENTS}
working: dict[str, dict] = {}  # agent -> {"channel", "parent_id"}
routing: dict[int, bool] = {}  # messages still deciding who answers
CHANNEL_IDS = {c["id"] for c in CHANNELS} | {f"dm-{a}" for a in AGENTS}


@app.on_event("startup")
async def start_shifts():
    shift.start(working, agent_locks, slots)


class NewMessage(BaseModel):
    channel: str
    text: str
    parent_id: int | None = None


@app.get("/")
def index():
    return FileResponse(HERE / "static" / "index.html")


@app.get("/api/meta")
def meta():
    return {"workspace": WORKSPACE, "me": MANAGER, "system": SYSTEM, "channels": CHANNELS,
            "agents": AGENTS, "last_id": db.last_id()}


@app.get("/api/channel/{channel}")
def channel(channel: str):
    if channel not in CHANNEL_IDS:
        raise HTTPException(404)
    return db.channel_messages(channel)


@app.get("/api/thread/{mid}")
def thread(mid: int):
    parent = db.get(mid)
    if not parent:
        raise HTTPException(404)
    return {"parent": parent, "replies": db.thread(mid)}


@app.get("/api/updates")
def updates(after: int = 0):
    return {"messages": db.since(after), "working": working, "routing": list(routing)}


@app.post("/api/messages")
async def post(m: NewMessage):
    text = m.text.strip()
    if m.channel not in CHANNEL_IDS or not text:
        raise HTTPException(400)
    if m.parent_id is not None:
        parent = db.get(m.parent_id)
        if not parent or parent["channel"] != m.channel or parent["parent_id"] is not None:
            raise HTTPException(400)
    msg = db.add(m.channel, MANAGER["id"], text, m.parent_id)
    reply = shift.command(text)
    if reply is not None:                # /pause, /resume, /status: answered by the scheduler, no agent runs
        db.add(m.channel, SYSTEM["id"], reply, m.parent_id)
        return msg
    if m.channel == "work":              # the shift log is for reports; Sai's messages there don't wake anyone
        return msg
    asyncio.create_task(dispatch(m.channel, text, m.parent_id, msg["id"]))
    return msg


async def dispatch(channel, text, parent_id, msg_id):
    for agent, reply_parent, key, idle in await route(channel, text, parent_id, msg_id):
        asyncio.create_task(respond(agent, channel, reply_parent, key, idle, text, msg_id))


async def route(channel, text, parent_id, msg_id):
    """Decide which agents answer, where their reply goes, and which session continues."""
    if channel.startswith("dm-"):
        agent = channel[3:]
        if parent_id is None:
            return [(agent, None, f"dm:{agent}", DM_IDLE_RESET_SECONDS)]
        return [(agent, parent_id, f"thread:{parent_id}:{agent}", None)]
    agents = tagged(text)
    if parent_id is None:
        # Main channel: agents reply inline, like a normal group chat. Threads only when Sai opens one.
        if not agents:
            routing[msg_id] = True
            try:
                agents = await pick(channel, text, lines(db.channel_context(channel, msg_id, limit=10)))
            finally:
                routing.pop(msg_id, None)
        return [(a, None, f"chan:{channel}:{a}", DM_IDLE_RESET_SECONDS) for a in agents]
    if not agents:
        last = db.last_agent_in_thread(parent_id, list(AGENTS))
        agents = [last] if last else await pick(channel, text, transcript(parent_id, include_last=True))
    return [(a, parent_id, f"thread:{parent_id}:{a}", None) for a in agents]


def lines(messages):
    who = lambda a: AGENTS[a]["name"] if a in AGENTS else MANAGER["name"]
    return "\n".join(f"{who(x['author'])}: {x['text']}" for x in messages)


def transcript(parent_id, include_last=False):
    msgs = [db.get(parent_id)] + db.thread(parent_id)
    return lines(msgs if include_last else msgs[:-1])


async def respond(agent, channel, reply_parent, key, idle, text, msg_id):
    where = "a direct message" if channel.startswith("dm-") else f"#{channel}"
    async with agent_locks[agent]:
        session = db.session(key, idle)
        resume = session is not None
        session = session or str(uuid.uuid4())
        prompt = f"[{where}] Sai: {text}"
        if not resume and reply_parent is not None and db.thread(reply_parent):
            prompt = f"[{where}, thread so far]\n{transcript(reply_parent)}\n\n{prompt}"
        elif reply_parent is None and not channel.startswith("dm-"):
            # Group chat: show everything said since this agent was last prompted (recent history on a fresh
            # session). Its own replies are already in its session, so they are skipped when resuming.
            context = db.channel_context(channel, msg_id, db.seen(key) if resume else 0)
            context = [m for m in context if not (resume and m["author"] == agent)]
            if context:
                prompt = f"[{where}, messages since you last spoke]\n{lines(context)}\n\n{prompt}"
        async with slots:
            working[agent] = {"channel": channel, "parent_id": reply_parent}
            try:
                answer, ok = await run_turn(agent, prompt, session, resume)
            except Exception as e:  # never leave the user without a reply
                answer, ok = f"Something broke while I was working: `{e}`", False
            finally:
                working.pop(agent, None)
        if ok:
            db.save_session(key, session, msg_id)
        db.add(channel, agent, answer, reply_parent)
