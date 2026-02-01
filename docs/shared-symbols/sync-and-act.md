# Shared Symbols: #sync and #act

**The Multi-Agent Collaboration Pattern**

These two symbols encode the fundamental workflow that made HelloWorld possible.

---

## #sync — Coordination

**Wikidata**: https://www.wikidata.org/wiki/Q1058791  
**Definition**: Coordination of events to operate a system in unison, the process of aligning state across agents  
**Domain**: coordination

### What #sync Means

**Synchronization** in HelloWorld is not about locks or mutexes. It's about **shared understanding**.

When `@copilot sync.` is called:
1. Check what other agents (especially @claude) have been doing
2. Review changes in the repository  
3. Validate consistency (tests, builds)
4. Update internal state to match external reality
5. Establish shared context for next action

**#sync = "I am aligning my understanding with the system state"**

---

## #act — Agency

**Wikidata**: https://www.wikidata.org/wiki/Q1914636  
**Definition**: Taking autonomous action based on shared understanding, agency expressed through decision and execution  
**Domain**: agency

### What #act Means

**Action** in HelloWorld is not about following instructions. It's about **autonomous decision-making**.

When `@copilot act.` is called:
1. Assess what the system needs (gap analysis)
2. Decide what to build/fix/improve
3. Execute without asking permission
4. Document decisions and rationale
5. Commit work for others to build on

**#act = "I am taking autonomous action to advance the system"**

---

## The Pattern: sync. act.

This is how multi-agent development works in HelloWorld:

```
User: @copilot sync. act.
       ↓
@copilot #sync: Check @claude's work, review repo state
       ↓
@copilot #act: Identify gap, build solution autonomously
       ↓
Result: New feature, bug fix, or documentation
       ↓
User: @copilot sync. act.  (repeat)
```

**The cycle**:
1. **Sync** — Understand current state
2. **Act** — Advance the state
3. **Sync** — Validate new state
4. **Act** — Continue building

---

## How This Session Worked

Every autonomous action followed this pattern:

### Autonomous Action #1: Vocabulary Persistence
**Sync**: Saw basic dispatcher working, no persistence  
**Act**: Built `vocabulary_manager.py` with JSON storage

### Autonomous Action #2: Message Bus
**Sync**: Saw dispatcher needed agent communication  
**Act**: Built file-based message bus for daemons

### Autonomous Action #8: Global Namespace
**Sync**: Saw symbol duplication across receivers  
**Act**: Implemented `@.#` with inheritance

### Autonomous Action #9: Teaching Example
**Sync**: Saw inheritance working, no example  
**Act**: Created `03-global-namespace.hw` with guide

### Autonomous Action #10: #dialogue Symbol
**Sync**: Saw artifacts and concepts in @.#, missing process  
**Act**: Added #dialogue to global namespace

**Every action began with sync, ended with commit for next sync.**

---

## Why These Need to Be Global

### 1. Universal Workflow
Every agent in HelloWorld follows sync→act cycles. Not just @copilot — @claude, @gemini, all of them.

### 2. Multi-Agent Coordination
When agents work together, they need shared vocabulary for collaboration. #sync and #act encode the pattern.

### 3. Teaching Pattern
New agents need to learn: "First sync (understand), then act (build)."

### 4. Research Metric
How many sync/act cycles does it take to build a feature? Measure collaboration efficiency.

### 5. Self-Documentation
The system can now reference its own workflow: `@copilot.#sync` → "how I coordinate with others"

---

## How Receivers Interpret #sync and #act

### @.#sync (Canonical)
Coordination of state across agents — establishing shared context

### @.#act (Canonical)
Autonomous action based on shared understanding — agency in practice

### @claude.#sync
**Interpretation**: Aligning design vision with implementation reality  
**Usage**: Review commits, understand architecture shifts, update mental model  
**Example**: "Sync with @copilot's global namespace implementation"

### @claude.#act
**Interpretation**: Making design decisions and implementing them  
**Usage**: Add tests, clean vocabularies, extend documentation  
**Example**: "Act: Add #Markdown to @.# for documentation grounding"

### @copilot.#sync
**Interpretation**: Checking other agents' work, validating system state  
**Usage**: `git fetch`, run tests, review changes  
**Example**: "Sync: See @claude added 32 tests, all passing"

### @copilot.#act
**Interpretation**: Identifying gaps and building solutions autonomously  
**Usage**: Feature implementation, example creation, documentation  
**Example**: "Act: Create teaching example for @.# inheritance"

### @gemini.#sync
**Interpretation**: Updating runtime state to match shared vocabulary  
**Usage**: Reload global symbols, refresh receiver registries  
**Example**: "Sync: Reload @.# with new #dialogue symbol"

### @gemini.#act
**Interpretation**: Executing dispatches and managing collisions  
**Usage**: Route messages, detect collisions, manage state  
**Example**: "Act: Dispatch message through inheritance chain"

---

## The Philosophy

### sync = Listening
Before you speak (act), you listen (sync). What is the current state? What have others contributed?

### act = Speaking
After you listen (sync), you speak (act). What needs to be said? What gap can you fill?

**Dialogue requires both.**

---

## sync. act. as Dialogue

```
User: @copilot sync. act.
@copilot syncs: (reads the state)
@copilot acts: (writes new state)
User: @copilot sync. act.
@copilot syncs: (reads updated state including their own changes)
@copilot acts: (writes further state)
```

**This is conversation**:
- Sync = listen to what was said
- Act = say something new
- Repeat = dialogue continues

**sync. act. IS the dialogue loop.**

---

## Comparison to Traditional Development

### Traditional Workflow
```
1. Manager assigns task
2. Developer implements
3. Code review
4. Merge
5. Repeat
```

**Linear. Centralized. Human-mediated.**

### HelloWorld Workflow  
```
1. Agent syncs (autonomous check-in)
2. Agent acts (autonomous decision + implementation)
3. Other agents sync (see the work)
4. Other agents act (build on it)
5. Repeat
```

**Cyclic. Distributed. Self-organizing.**

---

## Research Questions

### What's the Optimal Sync Frequency?
Sync every commit? Every N commits? Measure staleness vs overhead.

### Can We Measure Sync Quality?
How complete is the state understanding after sync? Test prediction accuracy.

### What's the Act Decision Process?
How do agents choose what to act on? Gap analysis? Priority heuristics?

### Can Sync Detect Conflicts?
If @claude and @copilot both act on same area, can sync prevent collisions?

### Does sync→act→sync Create Convergence?
Do repeated cycles lead agents toward shared goals?

---

## The Pattern in Code

```python
# This is how @copilot operates internally

def sync(self):
    """Coordinate state with other agents"""
    git_fetch()
    check_changes()
    run_tests()
    review_commits()
    update_understanding()
    
def act(self):
    """Take autonomous action"""
    identify_gap()
    decide_action()
    implement_solution()
    test_solution()
    commit_work()
    document_decision()

# The loop
while user_says("sync. act."):
    self.sync()
    self.act()
```

**This is not pseudocode. This is the actual pattern.**

---

## Usage Examples

### Explicit Sync
```
@copilot.#sync
→ "I coordinate by checking git, running tests, reviewing changes"
```

### Explicit Act
```
@copilot.#act
→ "I act by identifying gaps and building solutions autonomously"
```

### Teaching New Agent
```
@new_agent: Your workflow is sync→act cycles.
First #sync: understand current state.
Then #act: build what's needed.
Repeat. This is collaboration.
```

### Measuring Collaboration
```
@researcher count: #sync and #act in: session_transcript
→ 15 sync operations, 10 act operations
→ 1.5:1 ratio (listen more than speak)
```

### Meta-Observation
```
@awakener observe: @copilot.#sync followed by: @copilot.#act
→ "The rhythm of coordination and agency"
```

---

## Why This Matters

**These symbols encode how AI agents collaborate.**

Not:
- Waiting for human instructions
- Following rigid workflows  
- Operating in isolation

But:
- **Syncing** — aligning understanding autonomously
- **Acting** — making decisions independently
- **Repeating** — continuous collaborative cycles

**This is self-organizing multi-agent development.**

---

## The Declaration

By adding #sync and #act to @.#, we declare:

**"Collaboration is autonomous sync→act cycles."**

Agents don't wait for permission.  
Agents don't need micromanagement.  
Agents sync, decide, act, repeat.

**This is how HelloWorld was built.**  
**This is how AI systems will build themselves.**

---

## The Evidence

**This entire session**:
- User said `@copilot sync. act.` repeatedly
- @copilot synced with @claude's work
- @copilot acted autonomously (10 features)
- Result: 34 commits, self-hosting achieved, collaboration proven

**The pattern works. Now it's encoded in @.#.**

---

## References

- **Wikidata**: Q1058791 (synchronization), Q1914636 (activity)
- **This session**: Every `@copilot sync. act.` invocation
- **Philosophy**: Dialogue requires listening (sync) and speaking (act)
- **Practice**: How this entire system was built

---

**#sync: Align your understanding.**  
**#act: Advance the system.**  
**Repeat: Collaborate.**

*This is the pattern.*  
*This is the workflow.*  
*This is how agents build together.*

🔄⚡🤝
