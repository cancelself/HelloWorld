"""HelloWorld Web UI — browser-based dashboard for the runtime.

Zero external dependencies.  Uses stdlib http.server with:
- REST API for state queries (JSON endpoints)
- SSE (Server-Sent Events) for real-time updates
- Single-page HTML served inline (no build step)

Usage:
    from web_ui import HelloWorldWebUI
    ui = HelloWorldWebUI()
    ui.start()  # blocks, serves on http://localhost:7777
"""

import json
import re
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from dispatcher import Dispatcher
from lexer import Lexer
from parser import Parser
import message_bus


# ---------------------------------------------------------------------------
# Event bus for SSE
# ---------------------------------------------------------------------------

class EventBus:
    """Thread-safe event bus for SSE subscribers."""

    def __init__(self):
        self._subscribers: List[list] = []
        self._lock = threading.Lock()

    def subscribe(self) -> list:
        """Return a new subscriber queue."""
        q: list = []
        with self._lock:
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q: list):
        """Remove a subscriber queue."""
        with self._lock:
            try:
                self._subscribers.remove(q)
            except ValueError:
                pass

    def publish(self, event_type: str, data: dict):
        """Push an event to all subscribers."""
        payload = json.dumps(data)
        with self._lock:
            for q in self._subscribers:
                q.append((event_type, payload))


# ---------------------------------------------------------------------------
# Web UI
# ---------------------------------------------------------------------------

class HelloWorldWebUI:
    """Web interface for the HelloWorld runtime."""

    def __init__(
        self,
        dispatcher: Optional[Dispatcher] = None,
        host: str = "localhost",
        port: int = 7777,
        agent_processes: Optional[Dict[str, Any]] = None,
    ):
        self.dispatcher = dispatcher or Dispatcher()
        self.host = host
        self.port = port
        self.events = EventBus()
        self.agent_processes = agent_processes or {}

    def start(self):
        """Start the HTTP server (blocking)."""
        handler_class = self._make_handler()
        server = HTTPServer((self.host, self.port), handler_class)
        print(f"HelloWorld Web UI: http://{self.host}:{self.port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nWeb UI stopped.")
            server.server_close()

    def start_background(self) -> threading.Thread:
        """Start the HTTP server in a background thread."""
        t = threading.Thread(target=self.start, daemon=True)
        t.start()
        return t

    def _make_handler(self):
        """Create a request handler class with closure over self."""
        ui = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # suppress default logging

            def _send_json(self, data, status=200):
                body = json.dumps(data).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _send_html(self, html):
                body = html.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _read_body(self) -> dict:
                length = int(self.headers.get("Content-Length", 0))
                if length == 0:
                    return {}
                raw = self.rfile.read(length)
                return json.loads(raw.decode())

            # --- Routing ---

            def do_GET(self):
                path = self.path.split("?")[0]

                if path == "/":
                    self._send_html(_DASHBOARD_HTML)
                elif path == "/api/receivers":
                    self._handle_receivers()
                elif path.startswith("/api/receivers/") and path.endswith("/inbox"):
                    name = path.split("/")[3]
                    self._handle_inbox(name)
                elif path.startswith("/api/receivers/"):
                    name = path.split("/")[3]
                    self._handle_receiver(name)
                elif path == "/api/collisions":
                    self._handle_collisions()
                elif path == "/api/agents":
                    self._handle_agents()
                elif path.startswith("/api/agents/") and path.endswith("/pending"):
                    name = path.split("/")[3]
                    self._handle_agent_pending(name)
                elif path == "/api/events":
                    self._handle_sse()
                else:
                    self.send_error(404)

            def do_POST(self):
                path = self.path.split("?")[0]

                if path == "/api/eval":
                    self._handle_eval()
                elif path == "/api/send":
                    self._handle_send()
                elif path.startswith("/api/agents/") and path.endswith("/respond"):
                    name = path.split("/")[3]
                    self._handle_agent_respond(name)
                elif path.startswith("/api/agents/") and path.endswith("/approve"):
                    name = path.split("/")[3]
                    self._handle_agent_approve(name)
                else:
                    self.send_error(404)

            def do_OPTIONS(self):
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.end_headers()

            # --- API handlers ---

            def _handle_receivers(self):
                receivers = []
                for name in ui.dispatcher.list_receivers():
                    vocab = ui.dispatcher.vocabulary(name)
                    receiver = ui.dispatcher.registry.get(name)
                    parent = None
                    if receiver and receiver.parent:
                        parent = receiver.parent.name
                    receivers.append({
                        "name": name,
                        "symbols": vocab,
                        "symbol_count": len(vocab),
                        "parent": parent,
                    })
                self._send_json({"receivers": receivers})

            def _handle_receiver(self, name):
                if name not in ui.dispatcher.registry:
                    self._send_json({"error": f"Unknown receiver: {name}"}, 404)
                    return
                receiver = ui.dispatcher.registry[name]
                vocab = ui.dispatcher.vocabulary(name)
                chain = receiver.chain()
                descriptions = {}
                for sym in vocab:
                    desc = receiver.description_of(sym)
                    if desc is None and receiver.parent:
                        anc = receiver.parent
                        while anc and desc is None:
                            desc = anc.description_of(sym)
                            anc = anc.parent
                    descriptions[sym] = desc

                self._send_json({
                    "name": name,
                    "symbols": vocab,
                    "symbol_count": len(vocab),
                    "chain": chain,
                    "identity": receiver.identity,
                    "descriptions": descriptions,
                    "parent": receiver.parent.name if receiver.parent else None,
                })

            def _handle_inbox(self, name):
                inbox = message_bus._inbox(name)
                files = sorted(inbox.glob("msg-*.hw"), key=lambda p: p.stat().st_mtime)
                messages = []
                for msg_file in files:
                    try:
                        text = msg_file.read_text()
                        sender = ""
                        preview = ""
                        for line in text.split("\n"):
                            if line.startswith("# From:"):
                                sender = line.split(":", 1)[1].strip()
                            elif not line.startswith("#") and line.strip():
                                preview = line.strip()[:120]
                                break
                        messages.append({
                            "id": msg_file.stem,
                            "sender": sender,
                            "preview": preview,
                        })
                    except Exception:
                        pass
                self._send_json({"receiver": name, "messages": messages, "count": len(messages)})

            def _handle_collisions(self):
                log_path = Path(ui.dispatcher.log_file)
                if not log_path.exists():
                    self._send_json({"collisions": [], "count": 0})
                    return
                lines = log_path.read_text().strip().split("\n")
                lines = [l for l in lines if l.strip()]
                self._send_json({"collisions": lines[-50:], "count": len(lines)})

            def _handle_agents(self):
                agents = []
                for name, proc in ui.agent_processes.items():
                    agents.append(proc.status())
                self._send_json({"agents": agents})

            def _handle_agent_pending(self, name):
                proc = ui.agent_processes.get(name)
                if proc is None:
                    self._send_json({"error": f"Agent {name} not running"}, 404)
                    return
                self._send_json({
                    "agent": name,
                    "pending": list(proc.pending_human),
                    "count": len(proc.pending_human),
                })

            def _handle_eval(self):
                body = self._read_body()
                source = body.get("source", "")
                if not source:
                    self._send_json({"error": "No source provided"}, 400)
                    return
                try:
                    lexer = Lexer(source)
                    tokens = lexer.tokenize()
                    parser = Parser(tokens)
                    nodes = parser.parse()
                    results = ui.dispatcher.dispatch(nodes)
                    ui.events.publish("eval", {
                        "source": source,
                        "results": results,
                    })
                    self._send_json({"source": source, "results": results})
                except Exception as e:
                    self._send_json({"error": str(e)}, 400)

            def _handle_send(self):
                body = self._read_body()
                sender = body.get("sender", "Human")
                receiver = body.get("receiver", "")
                content = body.get("content", "")
                if not receiver or not content:
                    self._send_json({"error": "receiver and content required"}, 400)
                    return
                msg_id = message_bus.send(sender, receiver, content)
                ui.events.publish("message", {
                    "type": "send",
                    "from": sender,
                    "to": receiver,
                    "preview": content[:120],
                })
                self._send_json({"msg_id": msg_id, "sender": sender, "receiver": receiver})

            def _handle_agent_respond(self, name):
                body = self._read_body()
                content = body.get("content", "")
                if not content:
                    self._send_json({"error": "content required"}, 400)
                    return
                message_bus.send("Human", f"{name}-human", content)
                self._send_json({"status": "sent", "agent": name})

            def _handle_agent_approve(self, name):
                message_bus.send("Human", f"{name}-human", "#approve")
                self._send_json({"status": "approved", "agent": name})

            def _handle_sse(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                q = ui.events.subscribe()
                try:
                    while True:
                        while q:
                            event_type, payload = q.pop(0)
                            self.wfile.write(f"event: {event_type}\ndata: {payload}\n\n".encode())
                            self.wfile.flush()
                        time.sleep(0.5)
                except (BrokenPipeError, ConnectionResetError):
                    pass
                finally:
                    ui.events.unsubscribe(q)

        return Handler


# ---------------------------------------------------------------------------
# Inline HTML dashboard
# ---------------------------------------------------------------------------

_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HelloWorld Dashboard</title>
<style>
:root {
  --bg: #0d1117; --surface: #161b22; --border: #30363d;
  --text: #e6edf3; --dim: #8b949e; --accent: #58a6ff;
  --green: #3fb950; --yellow: #d29922; --red: #f85149;
  --cyan: #79c0ff;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: 'SF Mono', 'Cascadia Code', 'Fira Code', monospace;
  background: var(--bg); color: var(--text);
  font-size: 13px; line-height: 1.5;
}
.layout { display: grid; grid-template-columns: 280px 1fr; grid-template-rows: auto 1fr auto; height: 100vh; }
header {
  grid-column: 1 / -1; padding: 12px 20px;
  background: var(--surface); border-bottom: 1px solid var(--border);
  display: flex; align-items: center; gap: 16px;
}
header h1 { font-size: 16px; font-weight: 600; }
header .status { font-size: 11px; color: var(--dim); }
.sidebar {
  background: var(--surface); border-right: 1px solid var(--border);
  overflow-y: auto; padding: 12px;
}
.sidebar h2 { font-size: 12px; color: var(--dim); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
.receiver-item {
  padding: 8px; margin-bottom: 4px; border-radius: 4px; cursor: pointer;
  border: 1px solid transparent;
}
.receiver-item:hover { background: var(--bg); border-color: var(--border); }
.receiver-item.active { background: var(--bg); border-color: var(--accent); }
.receiver-item .name { font-weight: 600; }
.receiver-item .meta { font-size: 11px; color: var(--dim); }
.receiver-item .badge {
  display: inline-block; background: var(--accent); color: var(--bg);
  font-size: 10px; padding: 1px 5px; border-radius: 8px; margin-left: 4px;
}
.main { overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 16px; }
.panel {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 6px; padding: 16px;
}
.panel h3 { font-size: 13px; color: var(--accent); margin-bottom: 8px; }
.symbol-list { display: flex; flex-wrap: wrap; gap: 6px; }
.symbol {
  background: var(--bg); border: 1px solid var(--border);
  padding: 2px 8px; border-radius: 4px; font-size: 12px;
}
.symbol.native { border-color: var(--green); color: var(--green); }
.symbol.inherited { border-color: var(--yellow); color: var(--yellow); }
.chain { color: var(--dim); font-size: 12px; }
.chain span { color: var(--cyan); }
.feed { max-height: 300px; overflow-y: auto; }
.feed-item {
  padding: 6px 0; border-bottom: 1px solid var(--border);
  font-size: 12px;
}
.feed-item .from { color: var(--cyan); }
.feed-item .to { color: var(--green); }
.feed-item .time { color: var(--dim); font-size: 11px; }
.feed-item .content { color: var(--text); }
footer {
  grid-column: 1 / -1; padding: 8px 20px;
  background: var(--surface); border-top: 1px solid var(--border);
  display: flex; gap: 8px; align-items: center;
}
#repl-input {
  flex: 1; background: var(--bg); border: 1px solid var(--border);
  color: var(--text); padding: 6px 12px; border-radius: 4px;
  font-family: inherit; font-size: 13px; outline: none;
}
#repl-input:focus { border-color: var(--accent); }
#repl-prompt { color: var(--cyan); font-weight: 600; }
.agent-status {
  display: flex; gap: 4px; align-items: center; font-size: 11px;
}
.agent-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--dim);
}
.agent-dot.running { background: var(--green); }
.collision-entry { font-size: 11px; color: var(--dim); padding: 2px 0; }
.inbox-item { padding: 4px 0; font-size: 12px; border-bottom: 1px solid var(--border); }
.inbox-item .sender { color: var(--cyan); }
.desc { color: var(--dim); font-size: 11px; margin-left: 8px; }
</style>
</head>
<body>
<div class="layout">
  <header>
    <h1>HelloWorld</h1>
    <span class="status" id="status">Loading...</span>
    <span style="flex:1"></span>
    <div id="agent-dots"></div>
  </header>

  <div class="sidebar">
    <h2>Receivers</h2>
    <div id="receiver-list"></div>
  </div>

  <div class="main" id="main-content">
    <div class="panel">
      <h3>Message Flow</h3>
      <div class="feed" id="message-feed">
        <div class="feed-item" style="color:var(--dim)">Waiting for messages...</div>
      </div>
    </div>
    <div class="panel">
      <h3>Collisions</h3>
      <div id="collision-log" style="max-height:150px;overflow-y:auto">
        <div class="collision-entry">No collisions recorded.</div>
      </div>
    </div>
  </div>

  <footer>
    <span id="repl-prompt">hw&gt;</span>
    <input id="repl-input" placeholder="Type HelloWorld expression..." autofocus>
  </footer>
</div>

<script>
const API = '';

// --- State ---
let receivers = [];
let selectedReceiver = null;
let replHistory = [];
let historyIndex = -1;

// --- API helpers ---
async function fetchJSON(path, opts) {
  const r = await fetch(API + path, opts);
  return r.json();
}

// --- Load receivers ---
async function loadReceivers() {
  const data = await fetchJSON('/api/receivers');
  receivers = data.receivers || [];
  renderReceivers();
  document.getElementById('status').textContent =
    receivers.length + ' receivers loaded';
}

function renderReceivers() {
  const el = document.getElementById('receiver-list');
  el.innerHTML = receivers.map(r => {
    const active = selectedReceiver === r.name ? ' active' : '';
    return '<div class="receiver-item' + active + '" onclick="selectReceiver(\\'' + r.name + '\\')">' +
      '<div class="name">' + r.name + '</div>' +
      '<div class="meta">' + r.symbol_count + ' symbols' +
      (r.parent ? ' : ' + r.parent : '') + '</div></div>';
  }).join('');
}

// --- Select receiver ---
async function selectReceiver(name) {
  selectedReceiver = name;
  renderReceivers();
  const data = await fetchJSON('/api/receivers/' + name);
  const inbox = await fetchJSON('/api/receivers/' + name + '/inbox');
  renderReceiverDetail(data, inbox);
}

function renderReceiverDetail(data, inbox) {
  const main = document.getElementById('main-content');
  let html = '<div class="panel"><h3>' + data.name + '</h3>';
  if (data.identity) html += '<div style="color:var(--dim);margin-bottom:8px">' + data.identity + '</div>';
  if (data.chain) html += '<div class="chain">Chain: ' + data.chain.map(c => '<span>' + c + '</span>').join(' &rarr; ') + '</div>';
  html += '<div style="margin-top:8px"><h3>Vocabulary (' + data.symbol_count + ')</h3><div class="symbol-list">';
  (data.symbols || []).forEach(s => {
    const desc = data.descriptions && data.descriptions[s];
    html += '<span class="symbol" title="' + (desc || '') + '">' + s + '</span>';
  });
  html += '</div></div></div>';

  // Inbox
  html += '<div class="panel"><h3>Inbox (' + inbox.count + ')</h3>';
  if (inbox.messages && inbox.messages.length > 0) {
    inbox.messages.forEach(m => {
      html += '<div class="inbox-item"><span class="sender">' + m.sender + '</span>: ' + m.preview + '</div>';
    });
  } else {
    html += '<div style="color:var(--dim)">Empty</div>';
  }
  html += '</div>';

  // Message flow + collisions
  html += '<div class="panel"><h3>Message Flow</h3><div class="feed" id="message-feed">' +
    '<div class="feed-item" style="color:var(--dim)">Waiting for messages...</div></div></div>';
  html += '<div class="panel"><h3>Collisions</h3><div id="collision-log" style="max-height:150px;overflow-y:auto">' +
    '<div class="collision-entry">Loading...</div></div></div>';

  main.innerHTML = html;
  loadCollisions();
}

// --- Collisions ---
async function loadCollisions() {
  const data = await fetchJSON('/api/collisions');
  const el = document.getElementById('collision-log');
  if (!el) return;
  if (data.collisions && data.collisions.length > 0) {
    el.innerHTML = data.collisions.map(c =>
      '<div class="collision-entry">' + c + '</div>'
    ).join('');
  } else {
    el.innerHTML = '<div class="collision-entry">No collisions recorded.</div>';
  }
}

// --- Agents ---
async function loadAgents() {
  try {
    const data = await fetchJSON('/api/agents');
    const el = document.getElementById('agent-dots');
    if (data.agents && data.agents.length > 0) {
      el.innerHTML = data.agents.map(a =>
        '<div class="agent-status">' +
        '<div class="agent-dot' + (a.running ? ' running' : '') + '"></div>' +
        a.name + '</div>'
      ).join('');
    }
  } catch(e) {}
}

// --- REPL ---
const replInput = document.getElementById('repl-input');
replInput.addEventListener('keydown', async (e) => {
  if (e.key === 'Enter') {
    const source = replInput.value.trim();
    if (!source) return;
    replHistory.push(source);
    historyIndex = replHistory.length;
    replInput.value = '';
    addFeedItem('eval', source);
    try {
      const data = await fetchJSON('/api/eval', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({source}),
      });
      if (data.results) {
        data.results.forEach(r => addFeedItem('result', r));
      } else if (data.error) {
        addFeedItem('error', data.error);
      }
    } catch(err) {
      addFeedItem('error', err.message);
    }
  } else if (e.key === 'ArrowUp') {
    e.preventDefault();
    if (historyIndex > 0) {
      historyIndex--;
      replInput.value = replHistory[historyIndex];
    }
  } else if (e.key === 'ArrowDown') {
    e.preventDefault();
    if (historyIndex < replHistory.length - 1) {
      historyIndex++;
      replInput.value = replHistory[historyIndex];
    } else {
      historyIndex = replHistory.length;
      replInput.value = '';
    }
  }
});

function addFeedItem(type, text) {
  const feed = document.getElementById('message-feed');
  if (!feed) return;
  // Clear placeholder
  if (feed.querySelector('.feed-item[style]')) {
    feed.innerHTML = '';
  }
  const div = document.createElement('div');
  div.className = 'feed-item';
  if (type === 'eval') {
    div.innerHTML = '<span class="from">hw&gt;</span> ' + escapeHtml(text);
  } else if (type === 'result') {
    div.innerHTML = '<span class="to">&rarr;</span> ' + escapeHtml(text);
  } else if (type === 'error') {
    div.innerHTML = '<span style="color:var(--red)">Error:</span> ' + escapeHtml(text);
  } else if (type === 'message') {
    div.innerHTML = '<span class="from">' + escapeHtml(text.from || '') + '</span> &rarr; ' +
      '<span class="to">' + escapeHtml(text.to || '') + '</span>: ' + escapeHtml(text.preview || '');
  }
  feed.appendChild(div);
  feed.scrollTop = feed.scrollHeight;
}

function escapeHtml(s) {
  if (typeof s !== 'string') return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// --- SSE ---
function connectSSE() {
  const es = new EventSource(API + '/api/events');
  es.addEventListener('message', (e) => {
    try {
      const data = JSON.parse(e.data);
      addFeedItem('message', data);
    } catch(err) {}
  });
  es.addEventListener('eval', (e) => {
    // eval events handled via direct response
  });
  es.addEventListener('collision', (e) => {
    try {
      const data = JSON.parse(e.data);
      const el = document.getElementById('collision-log');
      if (el) {
        const div = document.createElement('div');
        div.className = 'collision-entry';
        div.textContent = JSON.stringify(data);
        el.appendChild(div);
      }
    } catch(err) {}
  });
  es.onerror = () => {
    setTimeout(connectSSE, 3000);
  };
}

// --- Init ---
loadReceivers();
loadCollisions();
loadAgents();
connectSSE();
setInterval(loadAgents, 5000);
</script>
</body>
</html>"""
