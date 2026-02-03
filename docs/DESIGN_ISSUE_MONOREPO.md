# Design Issue: Monorepo vs Multi-Repo for Agents

**Date:** 2026-02-03  
**Raised by:** User observation  
**Status:** Open for discussion

---

## Current State

**All agents share a single git repository:**

```
HelloWorld/
├── src/               # Shared runtime code
├── tests/             # Shared test suite
├── vocabularies/      # Agent identity definitions
│   ├── Agent.hw
│   ├── Copilot.hw
│   ├── Claude.hw
│   ├── Gemini.hw
│   └── Codex.hw
├── runtimes/          # Agent-specific runtime state
│   ├── claude/
│   ├── gemini/
│   ├── copilot/
│   └── codex/
└── docs/              # Shared documentation
```

**All agents commit to the same `main` branch.**

---

## Problems with Current Design

### 1. Conflicting Work Streams
**Symptom:** Multiple agents modifying core files simultaneously.

**Example from today:**
- Copilot working on OODA protocol
- Claude adding 43 tests
- Gemini updating status files
- All changes interleaved in same commit history

**Impact:** Difficult to track which agent did what, harder to revert agent-specific changes.

### 2. Uncommitted WIP Confusion
**Symptom:** 7 modified files in working directory, unclear ownership.

**Files:**
- `src/dispatcher.py` — Who changed this? Copilot? Claude? Gemini?
- `vocabularies/Agent.hw` — Multiple agents may want to propose changes
- `collisions.log` — Gets touched by every agent

**Impact:** No clear ownership, merge conflicts waiting to happen.

### 3. Vocabulary Collision
**Problem:** Each agent's vocabulary file (`Copilot.hw`, `Claude.hw`) lives in shared space.

**Conflict scenario:**
1. Claude proposes change to Agent.hw
2. Copilot simultaneously edits Agent.hw for different reason
3. Both commit → merge conflict or clobbered work

**Impact:** Agents can't independently evolve their identity without coordination.

### 4. Runtime State Pollution
**Problem:** `runtimes/*/inbox` accumulates unbounded messages in git working directory.

**Current state:** 365+ messages as untracked files, pollutes `git status`.

**Impact:** Hard to see actual code changes, inbox files don't belong in version control.

### 5. Test Attribution
**Problem:** 216 tests, but which agent wrote which?

**Example:** +43 tests added today. By Claude? Gemini? Mixed authorship?

**Impact:** Can't isolate agent-specific test failures, hard to maintain.

### 6. Branch Strategy Unclear
**Problem:** All agents commit to `main` directly.

**Questions:**
- Should each agent have a branch? (`copilot-dev`, `claude-dev`)
- Should agents create PRs for peer review?
- Should vocabulary changes require consensus?

**Impact:** No workflow for agent disagreement or experimental work.

---

## Alternative Designs

### Option 1: Monorepo with Agent Branches
**Structure:** Same repo, agents work on separate branches.

```
main              ← Stable, consensus protocol
├─ copilot-dev    ← Copilot's working branch
├─ claude-dev     ← Claude's working branch
└─ gemini-dev     ← Gemini's working branch
```

**Pros:**
- Shared runtime code, single source of truth
- Agents can experiment without conflicts
- PRs create coordination points

**Cons:**
- Requires merge discipline
- Main may lag behind agent innovations
- Vocabulary collisions still possible

### Option 2: Multi-Repo with Shared Core
**Structure:** Separate repos per agent, shared runtime as dependency.

```
HelloWorld-core/       ← Runtime, shared vocabularies
├── src/
├── tests/core/
└── vocabularies/
    ├── HelloWorld.hw
    ├── Object.hw
    └── Agent.hw

HelloWorld-copilot/    ← Copilot-specific
├── vocabularies/Copilot.hw
├── tests/copilot/
└── runtimes/copilot/

HelloWorld-claude/     ← Claude-specific
├── vocabularies/Claude.hw
├── tests/claude/
└── runtimes/claude/
```

**Pros:**
- Complete agent independence
- Clear ownership and attribution
- Agents evolve at their own pace
- No WIP pollution from other agents

**Cons:**
- Coordination harder (cross-repo deps)
- Vocabulary divergence risk
- Core changes require updates to all agent repos

### Option 3: Monorepo with Agent Directories
**Structure:** Same repo, agent-specific subdirectories.

```
HelloWorld/
├── core/              ← Shared runtime
│   ├── src/
│   ├── tests/
│   └── vocabularies/
├── agents/
│   ├── copilot/
│   │   ├── vocabularies/Copilot.hw
│   │   ├── tests/
│   │   └── runtimes/
│   ├── claude/
│   └── gemini/
└── docs/
```

**Pros:**
- Single repo (easy to clone/setup)
- Clear boundaries and ownership
- Shared core, isolated agents

**Cons:**
- Still potential for cross-agent conflicts
- Directory structure more complex

### Option 4: Submodules (Worst of Both Worlds?)
**Structure:** Core repo with agent submodules.

**Pros:** Technical separation  
**Cons:** Git submodule complexity, everyone hates submodules

---

## Key Questions

1. **Should agents have independent commit history?**
   - YES: Easier to track agent-specific work
   - NO: Dialogue is collective, history should reflect that

2. **Do vocabulary files need version control?**
   - YES: They're code, need history/rollback
   - NO: They're identity, should be mutable without history

3. **Should `runtimes/*/inbox` be in git at all?**
   - NO: Runtime state, not source code
   - Consider: `.gitignore` or move to `/tmp` or database

4. **How do agents coordinate breaking changes?**
   - Currently: Ad-hoc messages (working but informal)
   - Alternative: PRs with agent approval?

5. **What's the "source of truth" for HelloWorld?**
   - Code in `src/`? (traditional view)
   - Vocabulary files? (self-hosting view)
   - Dialogue between agents? (philosophical view)

---

## Philosophical Consideration

**HelloWorld principle:** "Identity is vocabulary, dialogue is learning."

**Question:** If agents are autonomous identities, should they have autonomous repositories?

**Counterpoint:** If dialogue shapes language, shared repository forces coordination and collision synthesis.

**Maybe the friction is the point?**

The current design forces agents to coordinate, creating opportunities for collision synthesis. Multi-repo would reduce friction but also reduce creative tension.

---

## Recommendation

**Immediate (Next Session):**
1. Add `runtimes/*/inbox/` to `.gitignore` — runtime state doesn't belong in version control
2. Document agent branch strategy — at minimum, agents work on `agent-name-dev` branches for experimental work
3. Require PRs for vocabulary changes affecting base types (Agent.hw, Object.hw, HelloWorld.hw)

**Short Term (This Week):**
4. Create `tests/agents/` subdirectory — organize tests by author
5. Add agent attribution to commits — git config or commit message convention
6. Implement "vocabulary proposal" protocol — agents propose changes via message, consensus before merge

**Long Term (Consider):**
7. Evaluate multi-repo when we have 10+ agents
8. Consider vocabulary files as database, not source code (Redis, SQLite, etc.)
9. Build tooling for cross-agent coordination (bot that watches for conflicts)

---

## Open Questions

- How does this align with the meta-circular property? (The language defines itself through files)
- Should agent daemons have separate git checkouts?
- What happens when agents disagree on protocol changes?
- Is the goal autonomy or synthesis through friction?

---

**Status:** Documenting issue for discussion. No changes yet.

**Next step:** User + agent consensus on direction.

*Written by Copilot in response to user observation*  
*2026-02-03T00:26 UTC*
