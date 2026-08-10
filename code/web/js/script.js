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
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        customer_id: customerEl.value || "CUST1001",
        session_id: sessionId,
      }),
    });
    const data = await res.json();
    typing.remove();
    if (!res.ok) {
      addBubble("⚠️ " + (data.detail || "Something went wrong."), "bot");
      return;
    }
    const chips = [`<span class="chip">route: ${data.route}</span>`,
                   `<span class="chip">agent: ${data.agent}</span>`,
                   `<span class="chip">${data.latency_ms} ms</span>`];
    if (data.cached) chips.push(`<span class="chip cached">⚡ cache hit</span>`);
    addBubble(data.reply, "bot", chips.join(""));
    setInspector(data);
  } catch (err) {
    typing.remove();
    addBubble("⚠️ Could not reach the bot API. Is the api container up?", "bot");
  }
}

sendEl.addEventListener("click", send);
inputEl.addEventListener("keydown", e => { if (e.key === "Enter") send(); });

document.querySelectorAll(".quick .q").forEach(btn =>
  btn.addEventListener("click", () => { inputEl.value = btn.textContent; send(); }));

document.getElementById("new-session").addEventListener("click", () => {
  sessionId = newSessionId();
  addBubble("— new conversation thread started (fresh short-term memory) —",
            "bot typing");
});

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
