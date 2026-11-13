const $ = (id) => document.getElementById(id);
const S = { meta: null, current: null, cache: {}, threadId: null, thread: [], lastId: 0, unread: {}, working: {}, routing: [] };

const api = async (path, opts) => {
  const r = await fetch(path, opts);
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json();
};

const person = (id) => S.meta.agents[id] ? { id, ...S.meta.agents[id] }
  : (S.meta.system && id === S.meta.system.id) ? S.meta.system : S.meta.me;
const escape = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const md = (s) => (window.marked && window.DOMPurify)
  ? DOMPurify.sanitize(marked.parse(s, { breaks: true, gfm: true }))
  : escape(s).replace(/\n/g, "<br>");
const time = (ts) => new Date(ts * 1000).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
const day = (ts) => new Date(ts * 1000).toLocaleDateString([], { weekday: "long", month: "long", day: "numeric" });
const modelName = (m) => (m || "").replace(/^claude-/, "").replace(/-(\d+)-(\d+)$/, " $1.$2").replace(/^./, (c) => c.toUpperCase());
const label = (ch) => ch.startsWith("dm-") ? S.meta.agents[ch.slice(3)].name : `# ${ch}`;

function avatar(p, cls = "avatar") {
  return `<div class="${cls}" style="background:${p.color}">${p.name[0]}</div>`;
}

function renderMessage(m, prev, inThread) {
  const p = person(m.author);
  const cont = prev && prev.author === m.author && m.ts - prev.ts < 300;
  const replies = !inThread && m.reply_count
    ? `<div class="replies" data-thread="${m.id}">${m.reply_count} ${m.reply_count === 1 ? "reply" : "replies"}
       <span>Last reply ${time(m.last_reply_ts)}</span></div>` : "";
  const action = inThread ? "" : `<button class="msg-action" data-thread="${m.id}" title="Reply in thread">💬<span> Reply in thread</span></button>`;
  return `<div class="msg${cont ? " cont" : ""}">${action}${avatar(p)}<div class="body">
    <div class="meta"><b>${escape(p.name)}</b><span class="role">${escape(p.role)}</span><time>${time(m.ts)}</time></div>
    <div class="text">${md(m.text)}</div>${replies}</div></div>`;
}

function renderList(list, inThread) {
  let html = "", prev = null, lastDay = null;
  for (const m of list) {
    const d = day(m.ts);
    if (d !== lastDay && !inThread) { html += `<div class="divider">${d}</div>`; prev = null; }
    lastDay = d;
    html += renderMessage(m, prev, inThread);
    prev = m;
  }
  return html;
}

function stickToBottom(el, fn) {
  const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
  fn();
  if (atBottom) el.scrollTop = el.scrollHeight;
}

function renderSidebar() {
  const ch = S.meta.channels.map((c) => item(c.id, `<span class="hash">#</span>${c.id}`)).join("");
  const dm = Object.entries(S.meta.agents).map(([id, a]) => {
    const busy = S.working[id] ? " busy" : "";
    return item(`dm-${id}`, `<div class="mini" style="background:${a.color}">${a.name[0]}<span class="dot${busy}"></span></div>${a.name}`);
  }).join("");
  $("view-list").firstElementChild.className = S.current === null ? "active" : "";
  $("channel-list").innerHTML = ch;
  $("dm-list").innerHTML = dm;
}

function item(id, inner) {
  const n = S.unread[id] || 0;
  const cls = [id === S.current ? "active" : "", n ? "unread" : ""].join(" ");
  return `<li class="${cls}" data-channel="${id}">${inner}${n ? `<span class="badge">${n}</span>` : ""}</li>`;
}

function renderMain() {
  if (S.current === null) { renderOfficeStatus(); return; }
  const list = S.cache[S.current] || [];
  const el = $("messages");
  stickToBottom(el, () => {
    el.innerHTML = list.length ? renderList(list, false)
      : `<div class="empty">This is the very beginning of ${escape(label(S.current))}.</div>`;
  });
  renderWorking();
}

function renderThread() {
  if (!S.threadId) return;
  const el = $("thread-messages");
  const [parent, ...replies] = S.thread;
  stickToBottom(el, () => {
    el.innerHTML = renderMessage(parent, null, true)
      + (replies.length ? `<div class="divider">${replies.length} ${replies.length === 1 ? "reply" : "replies"}</div>` : "")
      + renderList(replies, true);
  });
  renderWorking();
}

function renderOfficeStatus() {
  const busy = Object.entries(S.working).map(([a, w]) => `${S.meta.agents[a].name} (${label(w.channel)})`);
  $("topic").textContent = busy.length ? `Working: ${busy.join(", ")}` : "Everyone's free. Click someone to message them.";
}

function renderWorking() {
  if (S.current === null) { $("working").textContent = ""; return; }
  const names = (pred) => Object.entries(S.working).filter(([, w]) => pred(w)).map(([a]) => S.meta.agents[a].name);
  const line = (n) => n.length ? `${n.join(", ")} ${n.length === 1 ? "is" : "are"} working…` : "";
  const deciding = (S.cache[S.current] || []).some((m) => S.routing.includes(m.id));
  $("working").textContent = line(names((w) => w.channel === S.current)) || (deciding ? "Finding who should answer…" : "");
  $("thread-working").textContent = S.threadId ? line(names((w) => w.parent_id === S.threadId)) : "";
}

function setOfficeVisible(on) {
  $("office").classList.toggle("hidden", !on);
  for (const id of ["messages", "composer"]) $(id).classList.toggle("hidden", on);
  if (on) Office.start($("office-canvas"), S.meta, () => S.working, (agent) => openChannel(`dm-${agent}`));
  else Office.stop();
}

function openOffice() {
  S.current = null;
  $("app").classList.remove("nav-open");
  $("title").textContent = "🏢 Office";
  closeThread();
  setOfficeVisible(true);
  renderSidebar();
  renderOfficeStatus();
  history.replaceState(null, "", "#office");
}

async function openChannel(id) {
  setOfficeVisible(false);
  history.replaceState(null, "", `#${id}`);
  S.current = id;
  S.unread[id] = 0;
  $("app").classList.remove("nav-open");
  $("title").textContent = label(id);
  const c = S.meta.channels.find((x) => x.id === id);
  const ag = c ? null : S.meta.agents[id.slice(3)];
  $("topic").textContent = c ? c.topic : [ag.role, modelName(ag.model), ag.account].filter(Boolean).join(" · ");
  $("input").placeholder = `Message ${label(id)}`;
  closeThread();
  renderSidebar();
  S.cache[id] = await api(`/api/channel/${id}`);
  renderMain();
  $("messages").scrollTop = $("messages").scrollHeight;
  $("input").focus();
}

async function openThread(id) {
  const t = await api(`/api/thread/${id}`);
  S.threadId = id;
  S.thread = [t.parent, ...t.replies];
  $("thread-where").textContent = label(t.parent.channel);
  $("thread").classList.remove("hidden");
  renderThread();
  $("thread-messages").scrollTop = $("thread-messages").scrollHeight;
  $("thread-input").focus();
}

function closeThread() {
  S.threadId = null;
  $("thread").classList.add("hidden");
}

async function send(text, parentId) {
  if (!text.trim()) return;
  await api("/api/messages", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ channel: S.current, text, parent_id: parentId }),
  });
  await poll();
}

function ingest(m) {
  if (S.meta.agents[m.author]) Office.say(m.author, m.text);
  if (m.parent_id === null) {
    const list = S.cache[m.channel];
    if (list && !list.some((x) => x.id === m.id)) list.push(m);
    if (m.channel !== S.current && m.author !== S.meta.me.id) S.unread[m.channel] = (S.unread[m.channel] || 0) + 1;
  } else {
    const parent = (S.cache[m.channel] || []).find((x) => x.id === m.parent_id);
    if (parent) { parent.reply_count = (parent.reply_count || 0) + 1; parent.last_reply_ts = m.ts; }
    if (m.parent_id === S.threadId && !S.thread.some((x) => x.id === m.id)) S.thread.push(m);
    if (m.channel !== S.current && m.author !== S.meta.me.id) S.unread[m.channel] = (S.unread[m.channel] || 0) + 1;
  }
}

let polling = false;
async function poll() {
  if (polling) return;
  polling = true;
  try {
    const u = await api(`/api/updates?after=${S.lastId}`);
    u.messages.forEach((m) => { ingest(m); S.lastId = Math.max(S.lastId, m.id); });
    const changed = u.messages.length || JSON.stringify([u.working, u.routing]) !== JSON.stringify([S.working, S.routing]);
    S.working = u.working;
    S.routing = u.routing || [];
    if (changed) { renderSidebar(); renderMain(); renderThread(); }
  } catch (e) { console.warn(e); }
  polling = false;
}

function wireComposer(form, input, parent) {
  const submit = () => { const t = input.value; input.value = ""; resize(input); send(t, parent()); };
  form.addEventListener("submit", (e) => { e.preventDefault(); submit(); });
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); submit(); }
  });
  input.addEventListener("input", () => resize(input));
}
const resize = (t) => { t.style.height = "auto"; t.style.height = `${t.scrollHeight}px`; };

async function main() {
  S.meta = await api("/api/meta");
  S.lastId = S.meta.last_id;
  document.title = S.meta.workspace;
  $("ws-name").textContent = S.meta.workspace;
  document.addEventListener("click", (e) => {
    const ch = e.target.closest("[data-channel]");
    if (ch) openChannel(ch.dataset.channel);
    if (e.target.closest("[data-view]")) openOffice();
    const th = e.target.closest("[data-thread]");
    if (th) openThread(Number(th.dataset.thread));
  });
  $("thread-close").onclick = closeThread;
  $("menu").onclick = () => $("app").classList.toggle("nav-open");
  wireComposer($("composer"), $("input"), () => null);
  wireComposer($("thread-composer"), $("thread-input"), () => S.threadId);
  S.working = (await api(`/api/updates?after=${S.lastId}`)).working;   // so busy agents start at their desks
  const start = location.hash.slice(1);
  if (start === "office") openOffice();
  else await openChannel(S.meta.channels.some((c) => c.id === start) || start.startsWith("dm-") ? start : "general");
  setInterval(poll, 1500);
}
main();
