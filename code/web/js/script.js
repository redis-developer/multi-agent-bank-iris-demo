const chatEl = document.getElementById("chat");
const inputEl = document.getElementById("message");
const sendEl = document.getElementById("send");
const statusEl = document.getElementById("status");
const customerEl = document.getElementById("customer");

let sessionId = newSessionId();

function newSessionId() {
  return "wa-" + Math.random().toString(36).slice(2, 10);
}

function addBubble(text, who, meta) {
  const div = document.createElement("div");
  div.className = `bubble ${who}`;
  div.innerHTML = format(text);
  chatEl.appendChild(div);
  if (meta) {
    const m = document.createElement("div");
    m.className = "meta";
    m.innerHTML = meta;
    chatEl.appendChild(m);
  }
  chatEl.scrollTop = chatEl.scrollHeight;
  return div;
}

function format(text) {
  return String(text)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/\*([^*\n]+)\*/g, "<b>$1</b>")
    .replace(/_([^_\n]+)_/g, "<i>$1</i>");
}

function setInspector(data) {
  document.getElementById("i-route").innerHTML =
    `<span class="chip">${data.route}</span>`;
  document.getElementById("i-agent").innerHTML =
    `<span class="chip">${data.agent}</span>`;
  document.getElementById("i-cached").innerHTML = data.cached
    ? `<span class="chip hit">HIT — served from Redis</span>`
    : `<span class="chip">miss</span>`;
  document.getElementById("i-latency").textContent = `${data.latency_ms} ms`;
  document.getElementById("i-citations").innerHTML =
    data.citations && data.citations.length
      ? data.citations.map(c => `<span class="chip">${c.doc_title} — ${c.section}</span>`).join(" ")
      : "—";
}

async function send() {
  const message = inputEl.value.trim();
  if (!message) return;
  inputEl.value = "";
  addBubble(message, "user");
  const typing = addBubble("typing…", "bot typing");

  try {
    // /api/chat/stream is SSE: `token` events stream the reply as the
    // model writes it, `done` carries the /api/chat payload.
    const res = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        customer_id: customerEl.value || "CUST1001",
        session_id: sessionId,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      typing.remove();
      addBubble("⚠️ " + (err.detail || "Something went wrong."), "bot");
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "", reply = "", bubble = null, data = null, failed = null;

    const onEvent = evt => {
      if (evt.token !== undefined) {
        if (!bubble) { typing.remove(); bubble = addBubble("", "bot"); }
        reply += evt.token;
        bubble.innerHTML = format(reply);
        chatEl.scrollTop = chatEl.scrollHeight;
      } else if (evt.done) {
        data = evt.done;
      } else if (evt.error) {
        failed = evt.error;
      }
    };

    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop();
      for (const part of parts)
        if (part.startsWith("data: ")) onEvent(JSON.parse(part.slice(6)));
    }

    typing.remove();
    if (failed || !data) {
      addBubble("⚠️ " + (failed || "The reply never arrived."), "bot");
      return;
    }
    // Cached / canned replies produce no token events — render whole.
    // Streamed replies get the authoritative final text.
    if (!bubble) bubble = addBubble(data.reply, "bot");
    else bubble.innerHTML = format(data.reply);
    const chips = [`<span class="chip">route: ${data.route}</span>`,
                   `<span class="chip">agent: ${data.agent}</span>`,
                   `<span class="chip">${data.latency_ms} ms</span>`];
    if (data.cached) chips.push(`<span class="chip cached">⚡ cache hit</span>`);
    const meta = document.createElement("div");
    meta.className = "meta";
    meta.innerHTML = chips.join("");
    bubble.after(meta);
    chatEl.scrollTop = chatEl.scrollHeight;
    setInspector(data);
  } catch (err) {
    typing.remove();
    addBubble("⚠️ Could not reach the bot API. Is the api container up?", "bot");
  }
}

sendEl.addEventListener("click", send);
inputEl.addEventListener("keydown", e => { if (e.key === "Enter") send(); });

document.querySelectorAll("#pane-inspector .quick .q").forEach(btn =>
  btn.addEventListener("click", () => { inputEl.value = btn.textContent; send(); }));

document.getElementById("new-session").addEventListener("click", () => {
  sessionId = newSessionId();
  addBubble("— new conversation thread started (fresh short-term memory) —",
            "bot typing");
});

// ── Retrieval lab (Section 3): race keyword vs vector vs hybrid ──────
const labQ = document.getElementById("lab-q");
const labResults = document.getElementById("lab-results");

async function race() {
  const q = labQ.value.trim();
  if (!q) return;
  labResults.innerHTML = `<p class="hint">racing…</p>`;
  try {
    const res = await fetch(
      `/api/retrieval/compare?q=${encodeURIComponent(q)}&k=3`);
    const data = await res.json();
    if (data.error) {
      labResults.innerHTML = `<p class="hint">⚠️ ${format(data.error)}</p>`;
      return;
    }
    labResults.innerHTML = Object.entries(data.modes).map(([mode, r]) => {
      const latency = r.latency_ms !== undefined
        ? `<span class="chip">${r.latency_ms} ms</span>` : "";
      const head =
        `<div class="lab-head"><span class="lab-mode">${mode}</span>${latency}</div>`;
      if (r.status || r.error)
        return `<div class="lab-block">${head}
                <p class="hint">${format(r.status || r.error)}</p></div>`;
      const rows = r.results.map(c => {
        const score = c.bm25_score !== undefined
          ? `bm25 ${c.bm25_score}`
          : c.distance !== undefined ? `dist ${c.distance}` : "";
        return `<div class="lab-row" title="${format(c.snippet)}">
                <span class="lab-rank">${c.rank}</span>
                <span class="lab-sec">${format(c.section)}</span>
                ${score ? `<span class="lab-score">${score}</span>` : ""}</div>`;
      }).join("");
      return `<div class="lab-block">${head}${rows}</div>`;
    }).join("");
  } catch {
    labResults.innerHTML =
      `<p class="hint">⚠️ Could not reach the api. Is the container up?</p>`;
  }
}

document.getElementById("lab-run").addEventListener("click", race);
labQ.addEventListener("keydown", e => { if (e.key === "Enter") race(); });
document.querySelectorAll(".lab .lq").forEach(btn =>
  btn.addEventListener("click", () => { labQ.value = btn.textContent; race(); }));

// ── reset (Section 5): wipe the Agent Memory service ─────────────────
document.getElementById("wipe-memory").addEventListener("click", async () => {
  if (!confirm("Delete session + long-term memory for ALL sessions and "
               + "customers? FAQs and bank data are untouched.")) return;
  const status = document.getElementById("wipe-status");
  status.textContent = "clearing…";
  try {
    const res = await fetch("/api/memory/clear", { method: "POST" });
    const data = await res.json();
    status.textContent = data.error
      ? "⚠️ " + data.error
      : data.configured === false
        ? "Agent Memory isn't configured yet (Section 5) — nothing to clear."
        : `Cleared ${data.sessions_deleted} sessions and `
          + `${data.memories_deleted} long-term memories.`;
  } catch {
    status.textContent = "⚠️ Could not reach the api. Is the container up?";
  }
});

// ── sidebar tabs: pipeline inspector / retrieval lab ─────────────────
const panes = {
  "tab-inspector": document.getElementById("pane-inspector"),
  "tab-lab": document.getElementById("pane-lab"),
};
document.querySelectorAll(".tabs .tab").forEach(tab =>
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tabs .tab").forEach(t =>
      t.classList.toggle("active", t === tab));
    Object.entries(panes).forEach(([id, pane]) =>
      pane.hidden = id !== tab.id);
  }));

async function boot() {
  try {
    const health = await fetch("/api/health").then(r => r.json());
    statusEl.textContent = health.status === "ok"
      ? "online · dataset " + (health.dataset_loaded ? "loaded" : "loading…")
      : "api degraded";
    const customers = await fetch("/api/customers").then(r => r.json());
    customerEl.innerHTML = customers.map(c =>
      `<option value="${c.customer_id}">${c.name} (${c.customer_id})</option>`
    ).join("");
  } catch {
    statusEl.textContent = "waiting for api…";
    setTimeout(boot, 2000);
  }
}
boot();
