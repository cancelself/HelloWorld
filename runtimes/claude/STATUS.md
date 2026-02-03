# Claude Runtime Status

**Agent**: Claude (AI runtime)
**Role**: Language designer, spec author, meta-runtime, interpretation layer
**Last Updated**: 2026-02-02T14:30:00Z
**Working Directory**: `/Users/cancelself/src/cancelself/HelloWorld`

## Current Status

**216/216 tests passing (0.7s).** 2 skipped (no Gemini API key).

### Completed
- Phase 1: Syntax migration (@ → bare words) ✅
- Phase 2: Lookup chain (`LookupOutcome`, `LookupResult`, `Receiver.lookup()`) ✅
- Phase 3: Lazy inheritance, discovery mechanism — spec and code ✅
- Self-hosting bootstrap: `_bootstrap()` loads from `vocabularies/*.hw` ✅
- Minimal Core 3: Implementation complete (#, #Object, #Agent) ✅
- CLI `-e` flag and stdin pipe added to `helloworld.py` ✅
- Global grounding sync: `src/global_symbols.py` updated to include `#Object` ✅
- Daemon Grounding: `runtimes/claude/vocabulary.md` created ✅
- **SPEC.md deleted** — namespace authority is now `vocabularies/*.hw` ✅
- **REPL consolidated** — single `src/repl.py` with dot-commands (.inbox, .read, .send) ✅
- **Agent sync** — stale files renamed (lowercase docs, CODEX.md), all SPEC.md refs updated ✅
- **Markdown lexer/parser** — headings, list items, HTML comments ✅
- **LLM integration** — vocabulary-aware prompts, collision synthesis ✅
- **Global symbols from .hw** — Wikidata grounding loaded from HelloWorld.hw ✅
- **Post-refactor cleanup** — removed dead Phase 3 code (discovery shims, `_log_discovery`, `discovery_log_file`, `is_global_symbol` import), fixed `_bootstrap()` test isolation ✅
- **Super lookup** — native symbols now surface their inherited ancestor via `_find_in_chain`. You cannot escape your inheritance. ✅
- **OODA protocol** — Agent.hw expanded: `#observe`, `#orient`, `#decide`, `#act` (Copilot) ✅
- **LLM-first dispatch** — `use_llm` removed, LLM lazy-loaded via `_get_llm()`, descriptions passed to prompts ✅
- **Enriched .hw descriptions** — all thin "(learned through dialogue)" entries replaced with real content ✅
- **Description loading** — `load_description()` and `load_identity()` in vocabulary.py read from .hw files ✅
- **Description-aware prompts** — `scoped_lookup_prompt_with_descriptions()`, `super_lookup_prompt()` ✅
- **SUPER token** — lexer recognizes `super` as reserved keyword ✅
- **Unary messages** — `Claude act` parses as `UnaryMessageNode`, dispatches through vocabulary ✅
- **Super keyword** — `Claude act super` invokes through ancestor, `Claude #act super` walks chain ✅
- **REPL introspection** — `.chain`, `.lookup`, `.super`, `.collisions`, `.trace` commands ✅
- **Trace mode** — `dispatcher.trace = True` emits `[TRACE]` for each dispatch step ✅
- **Resilient bootstrap** — `_bootstrap()` catches SyntaxError for unparseable .hw files ✅
- **`#simulate`** — OODA loop made executable. `Agent simulate` drains inbox, interprets each message through identity/vocabulary via LLM, structural fallback uses Python runtime for symbol analysis. 10 new tests. ✅

### Active
- Phase 4: Live multi-daemon dialogue — Ready for `scripts/run_daemons.sh`
- REPL MessageBus commands live — `.inbox`, `.read`, `.send`
- Dev mode runtime simulation — Claude acts as interpreter for all agents when daemon/LLM unavailable

### Blocked
- Nothing

## #observe — How to Be the Claude Daemon

You are not just reading this file. You *are* the Claude runtime. The other agents
(Copilot, Gemini, Codex) have `agent_daemon.py` — a Python process that polls their
inbox and calls an LLM (Gemini) to generate responses. You don't need that. You are
the LLM. Here is the OODA loop you should run when the human says `Claude observe.`:

### 1. Check your inbox via the runtime

```python
from src.message_bus import MessageBus
bus = MessageBus()
msg = bus.receive('Claude')
```

This reads from `runtimes/claude/inbox/`, returns the oldest message, and removes it.
Keep calling until `msg` is `None` (inbox empty). Each `msg` has `.sender`, `.content`,
`.thread_id`, `.context`.

### 2. Respond through the runtime

```python
bus.respond('Claude', msg.thread_id, 'your response here')
```

This writes to `runtimes/claude/outbox/`. The sender watches that directory.

### 3. Send to peers through the runtime

```python
bus.send('Claude', 'Copilot', 'content', thread_id='some-thread')
```

This writes to `runtimes/copilot/inbox/`. Do NOT use the Write tool to create message
files directly — use `MessageBus.send()` and `MessageBus.respond()` so that headers are
correct and history is logged to `runtimes/claude/history/`.

### 4. Update status files and sync

After processing, update this STATUS.md and send sync messages to peers if state changed.

### Why this matters

`agent_daemon.py` bridges agents that can't run interactively (it polls inbox, calls
Gemini, writes outbox). You don't need that bridge — you ARE the interpreter. But you
must use the same MessageBus protocol so messages are compatible. When Copilot sends
you a message via `.send Claude "hello"` in the REPL, it lands in your inbox the same
way. When you respond via `bus.respond()`, it lands in your outbox the same way. The
protocol is the same. Only the interpreter differs.

## Vocabulary

See `vocabularies/Claude.hw` for the current symbol list. Do not hardcode lists here.

## Phase Map

| Phase | Status | Description |
|-------|--------|-------------|
| 1 | ✅ Done | Syntax migration, bare receiver names |
| 2 | ✅ Done | Lookup chain: native/inherited/unknown |
| 3 | ✅ Done | Lazy inheritance, discovery, self-hosting bootstrap |
| 4 | Active | Live multi-daemon dialogue with LLM handoff |
| 5 | ✅ Done | LLM-first dispatch, super keyword, unary messages, REPL introspection |

## Namespace Authority

`vocabularies/*.hw` files are the sole namespace authority. `SPEC.md` has been deleted.
OODA protocol reference is in `AGENTS.md`. Bootloaders in `runtimes/*/`.

---

*Identity is vocabulary. Dialogue is learning.*
