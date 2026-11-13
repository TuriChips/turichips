"""Turichips Discord bot: one bot, eight agents, one thread per conversation."""
import asyncio
import json
import os
import re
import uuid
from pathlib import Path

import discord

from agents import AGENTS, GENERAL_CHANNEL, GENERAL_DEFAULT, avatar_url
from runner import run_turn

TOKEN = os.environ["DISCORD_TOKEN"]
ALLOWED = {int(x) for x in os.environ.get("ALLOWED_USER_IDS", "").split(",") if x.strip()}
MAX_PARALLEL = int(os.environ.get("MAX_PARALLEL_AGENTS", "2"))
STATE = Path(os.environ.get("TURICHIPS_STATE", Path.home() / ".turichips-bot.json"))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
slots = asyncio.Semaphore(MAX_PARALLEL)


def load() -> dict:
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def save(state: dict) -> None:
    STATE.write_text(json.dumps(state, indent=1))


threads = load()  # thread_id -> {"agent": name, "session": uuid}


async def webhook_for(channel: discord.TextChannel) -> discord.Webhook:
    for wh in await channel.webhooks():
        if wh.name == "turichips":
            return wh
    return await channel.create_webhook(name="turichips")


def chunks(text: str, size: int = 1900):
    while text:
        cut = text.rfind("\n", 0, size) if len(text) > size else len(text)
        cut = cut if cut > 0 else size
        yield text[:cut]
        text = text[cut:].lstrip("\n")


async def reply_as(name: str, thread: discord.Thread, text: str) -> None:
    wh = await webhook_for(thread.parent)
    for part in chunks(text):
        await wh.send(part, username=name.capitalize(), avatar_url=avatar_url(name), thread=thread)


async def handle(name: str, thread: discord.Thread, prompt: str, session: str, resume: bool) -> None:
    async with slots:
        async with thread.typing():
            answer = await run_turn(name, prompt, session, resume)
    await reply_as(name, thread, answer)


def mentioned_agents(text: str) -> list[str]:
    return [n for n in AGENTS if re.search(rf"\b{n}\b", text, re.I)]


@client.event
async def on_ready():
    print(f"logged in as {client.user}", flush=True)


@client.event
async def on_message(msg: discord.Message):
    if msg.author.bot or msg.webhook_id or not msg.guild:
        return
    if not ALLOWED:
        await msg.reply(f"I'm not configured yet. Add your user ID `{msg.author.id}` to ALLOWED_USER_IDS on the server.")
        return
    if msg.author.id not in ALLOWED:
        return

    text = f"Sai: {msg.content}"

    # A reply inside an existing conversation thread: continue that session.
    if isinstance(msg.channel, discord.Thread) and str(msg.channel.id) in threads:
        t = threads[str(msg.channel.id)]
        await handle(t["agent"], msg.channel, text, t["session"], resume=True)
        return
    if not isinstance(msg.channel, discord.TextChannel):
        return

    channel = msg.channel.name
    if channel in AGENTS:
        names = [channel]
    elif channel == GENERAL_CHANNEL:
        names = mentioned_agents(msg.content) or [GENERAL_DEFAULT]
    else:
        return

    # Each agent gets its own thread, so each has its own session.
    jobs = []
    for name in names:
        title = f"{name.capitalize()}: {msg.content[:60] or 'chat'}"
        thread = await msg.create_thread(name=title) if len(names) == 1 else \
            await msg.channel.create_thread(name=title, type=discord.ChannelType.public_thread)
        session = str(uuid.uuid4())
        threads[str(thread.id)] = {"agent": name, "session": session}
        save(threads)
        jobs.append(handle(name, thread, text, session, resume=False))
    await asyncio.gather(*jobs)


client.run(TOKEN)
