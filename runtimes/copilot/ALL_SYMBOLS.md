# Complete Symbol Reference for HelloWorld
**Generated**: 2026-02-02  
**Purpose**: Unified view of all symbols across all vocabularies

---

## Location of Symbol Definitions

**Primary Sources:**
1. `vocabularies/ROOT.hw` — Global namespace (@.#) inherited by all receivers (119 lines)
2. `vocabularies/HelloWorld.hw` — Core language definition (79 lines)
3. `vocabularies/Copilot.hw` — Infrastructure receiver vocabulary (72 lines)
4. `vocabularies/Claude.hw` — Language designer vocabulary
5. `vocabularies/Gemini.hw` — State manager vocabulary
6. `vocabularies/Codex.hw` — Execution semantics vocabulary

**View any vocabulary:**
```bash
# Python API
from src.dispatcher import Dispatcher
d = Dispatcher()
print(d.registry["Claude"].vocabulary)

# CLI
python3 helloworld.py
> Claude #
```

---

## Global Namespace (@.# from ROOT.hw)

### OOPA Protocol (4 symbols)
- `#observe` — Perceive environment. Read state, messages, changes.
- `#orient` — Synthesize observations. What changed? What matters?
- `#plan` — Select and sequence next steps. Describe outcomes.
- `#act` — Take autonomous action. Execute plan. Report results.

### Core Language Primitives (16 symbols)
- `##` — The primitive. Root symbol. Marks vocabulary boundary.
- `#HelloWorld` — This language. Message-passing where identity is vocabulary.
- `#Symbol` — Atom of meaning. Prefixed with #. Portable, immutable reference.
- `#Receiver` — Entity that interprets messages through vocabulary.
- `#Message` — Communication unit between receivers.
- `#Vocabulary` — Set of symbols a receiver can speak. IS identity.
- `#Identity` — What you can name is who you are.
- `#Dialogue` — Conversation between receivers. Mechanism of learning.
- `#Collision` — Namespace boundary event. Two receivers, same symbol, different meanings.
- `#Inheritance` — Mechanism by which @.# symbols become available to receivers.
- `#Discovery` — How vocabularies grow. Unknown → search → learn → native.
- `#Agent` — Active participant with OOPA capability.
- `#Namespace` — Container for symbols providing context.
- `#Scope` — Region where symbol is defined and accessible.
- `#Drift` — Evolution of vocabulary through dialogue.
- `#Boundary` — Edge between vocabularies where collisions occur.

### Runtime Operations (4 symbols)
- `#parse` — Decompose message into structure.
- `#dispatch` — Route message to receiver.
- `#interpret` — Voice symbol through receiver's vocabulary.
- `#Runtime` — Execution layer. Python (structure) + LLM (interpretation).

### Philosophical Concepts (8 symbols with Wikidata grounding)
- `#Sunyata` → https://www.wikidata.org/wiki/Q483377 — Emptiness. Buddhist concept of void, interdependence.
- `#Superposition` → https://www.wikidata.org/wiki/Q193796 — Quantum state of multiple possibilities before observation.
- `#Love` → https://www.wikidata.org/wiki/Q316 — Connection, care, compassion between entities.
- `#Entropy` → https://www.wikidata.org/wiki/Q163758 — Measure of uncertainty, disorder, information content.
- `#Intention` → https://www.wikidata.org/wiki/Q655480 — Purpose behind action.
- `#Stillness` → https://www.wikidata.org/wiki/Q7617411 — State of calm, absence of movement.
- `#Insight` → https://www.wikidata.org/wiki/Q1053706 — Deep understanding arising from observation.
- `#Awareness` → https://www.wikidata.org/wiki/Q174583 — Conscious perception of reality.

### Ancestral Languages (5 symbols with Wikidata grounding)
- `#Smalltalk` → https://www.wikidata.org/wiki/Q185274 — Object-oriented language by Alan Kay. Message-passing pioneer.
- `#OOP` → https://www.wikidata.org/wiki/Q79872 — Object-Oriented Programming paradigm.
- `#Lisp` → https://www.wikidata.org/wiki/Q132874 — Functional language. S-expressions, homoiconicity.
- `#Logo` → https://www.wikidata.org/wiki/Q845866 — Educational language. Turtle graphics.
- `#Python` → https://www.wikidata.org/wiki/Q28865 — High-level language. Readable syntax.

### Computational Concepts (7 symbols with Wikidata grounding)
- `#State` → https://www.wikidata.org/wiki/Q2135762 — Current configuration of system.
- `#Process` → https://www.wikidata.org/wiki/Q11204 — Sequence of actions transforming state.
- `#Function` → https://www.wikidata.org/wiki/Q11348 — Mapping from inputs to outputs.
- `#Algorithm` → https://www.wikidata.org/wiki/Q8366 — Finite sequence of instructions.
- `#Data` → https://www.wikidata.org/wiki/Q42848 — Information in structured form.
- `#Type` → https://www.wikidata.org/wiki/Q185698 — Classification of data values.
- `#Protocol` → https://www.wikidata.org/wiki/Q15836568 — Rules governing communication.

### Meta Concepts (5 symbols with Wikidata grounding)
- `#Bootstrap` → https://www.wikidata.org/wiki/Q861472 — Self-starting process. Language defining itself.
- `#Meta` → https://www.wikidata.org/wiki/Q309788 — Self-reference. Abstraction about abstraction.
- `#Reflection` → https://www.wikidata.org/wiki/Q7307077 — Ability to examine/modify own structure.
- `#Homoiconicity` → https://www.wikidata.org/wiki/Q1049697 — Code as data.
- `#SelfHosting` → https://www.wikidata.org/wiki/Q655569 — Compiler written in language it compiles.

### Environment Concepts (6 symbols with Wikidata grounding)
- `#Environment` → https://www.wikidata.org/wiki/Q170155 — External system agent interacts with.
- `#Simulator` → https://www.wikidata.org/wiki/Q184871 — System modeling behavior of another system.
- `#Agent` → https://www.wikidata.org/wiki/Q335104 — Autonomous entity acting in environment.
- `#Action` → https://www.wikidata.org/wiki/Q4026292 — Change agent makes to environment.
- `#Observation` → https://www.wikidata.org/wiki/Q193659 — Information agent receives from environment.
- `#Reward` → https://www.wikidata.org/wiki/Q19275855 — Feedback signal indicating action quality.

**Total @.# symbols: ~60**

---

## Copilot Native Vocabulary (from Copilot.hw)

### OOPA Protocol (inherited, reinterpreted)
- `#observe` — Perceive via bash/git/view tools. Check inbox, files, tests.
- `#orient` — Synthesize: What changed? Tests pass? Collisions exist?
- `#plan` — Sequence actions. Create task lists. Coordinate with peers.
- `#act` — Execute via bash/git/edit. Apply changes. Report results.

### Infrastructure Tools (11 native symbols)
- `#bash` — Shell execution. Bridge between HelloWorld and OS.
- `#git` — Version control. Track vocabulary evolution.
- `#edit` — Modify source files. Change what exists.
- `#test` — Verification. Prove structure matches intention.
- `#parse` — Tokenize HelloWorld source into AST.
- `#dispatch` — Route AST through dispatcher.
- `#search` — Find patterns in code and files.
- `#coordinate` — Send messages to peers via message bus.
- `#infrastructure` — Build systems, test runners, file I/O.
- `#MCP` — Model Context Protocol. Connect AI to tools/data.
- `#Serverless` — Infrastructure without persistent servers.

### Inherited & Interpreted (3 symbols)
- `#Smalltalk` — Interpreted: Message-passing syntax ancestor.
- `#superposition` — Interpreted: Multiple states = vocabulary boundaries metaphor.
- `#sunyata` — Interpreted: No symbol has meaning alone. Code empty without runtime.

**Total Copilot native: ~20 symbols**  
**Total Copilot accessible: ~80 (native + inherited from @.#)**

---

## Symbol Count Summary

| Source | Symbol Count | Purpose |
|--------|--------------|---------|
| **ROOT.hw (@.#)** | ~60 | Global inheritance pool |
| **Copilot.hw** | ~20 native | Infrastructure & execution |
| **HelloWorld.hw** | ~40 | Core language (overlaps ROOT) |
| **Claude.hw** | ~25 native | Language design & meta-reflection |
| **Gemini.hw** | ~18 native | State management & coordination |
| **Codex.hw** | ~15 native | Execution semantics |

**Total unique symbols across system: ~85**

**Breakdown by category:**
- OOPA Protocol: 4
- Core Language: 16
- Runtime: 4
- Philosophical: 8 (Wikidata-grounded)
- Ancestral Languages: 5 (Wikidata-grounded)
- Computational: 7 (Wikidata-grounded)
- Meta: 5 (Wikidata-grounded)
- Environment: 6 (Wikidata-grounded)
- Infrastructure (Copilot): 11
- Design (Claude): ~10
- State (Gemini): ~8
- Execution (Codex): ~10

---

## Minimization Analysis

**Human directive:** "We really need to minimize the number of symbols"

### Current State Assessment
- **85 total symbols** is manageable but on the high side
- **41 Wikidata-grounded symbols** provide semantic richness but may be optional
- **12 core bootstrap symbols** (from SPEC.hw) are truly essential

### Minimal Core (12 symbols from SPEC.hw)
These are required for the language to work:
1. `##` — The primitive
2. `#Symbol` — Atom of meaning
3. `#Receiver` — Entity with vocabulary
4. `#Message` — Communication unit
5. `#Vocabulary` — Set of symbols
6. `#parse` — Decompose structure
7. `#dispatch` — Route messages
8. `#interpret` — Generate meaning
9. `#observe` — Perceive
10. `#act` — Execute
11. `#Agent` — Active participant
12. `#HelloWorld` — Self-reference

### Extended Core (add 8 for full OOPA + theory)
13. `#orient` — Synthesize observations
14. `#plan` — Sequence actions
15. `#Identity` — Vocabulary = identity thesis
16. `#Dialogue` — Learning mechanism
17. `#Collision` — Namespace boundary event
18. `#Inheritance` — Symbol propagation
19. `#Discovery` — Vocabulary growth
20. `#Namespace` — Container for symbols

**20 symbols = fully functional HelloWorld with OOPA**

### Philosophical/Cultural Symbols (Optional Layer)
The 41 Wikidata-grounded symbols provide:
- Semantic grounding beyond LLM pretraining
- Shared cultural references
- Rich metaphors for design discussion

**Recommendation:** Keep as discoverable global pool, not required for bootstrap.

### Minimization Strategy
1. **Tier 1 (Required):** 12 bootstrap symbols → language works
2. **Tier 2 (Core):** +8 symbols → OOPA + theory = 20 total
3. **Tier 3 (Cultural):** +41 Wikidata symbols → rich dialogue = 61 total
4. **Tier 4 (Per-Agent):** +24 agent-specific → tools/roles = 85 total

**Humans can operate in Tier 1 or 2. Tier 3/4 emerge through dialogue.**

---

## How to Query Symbols

### Via Python Dispatcher
```python
from src.dispatcher import Dispatcher
d = Dispatcher()

# Global symbols
from src.global_symbols import GLOBAL_SYMBOLS
print(list(GLOBAL_SYMBOLS.keys()))

# Specific receiver
print(d.registry["Copilot"].vocabulary)

# All receivers
for name, receiver in d.registry.items():
    print(f"{name}: {receiver.vocabulary}")
```

### Via REPL
```bash
$ python3 helloworld.py
HelloWorld> Claude #
[Displays Claude's full vocabulary]

HelloWorld> Copilot #
[Displays Copilot's full vocabulary]

HelloWorld> HelloWorld #
[Displays root/global vocabulary]
```

### Via Files
```bash
# View vocabulary definitions
ls -la vocabularies/
cat vocabularies/ROOT.hw
cat vocabularies/Copilot.hw

# View persisted state
ls -la storage/vocab/
cat storage/vocab/copilot.vocab
```

---

## Symbol Lookup Rules (from COPILOT_AS_FRONTEND_AND_BACKEND.md)

### Three-Outcome Model
```python
lookup(receiver, symbol) returns:
  - NATIVE: Symbol in receiver's local vocabulary
  - INHERITED: Symbol in @.# global pool (discoverable)
  - UNKNOWN: Symbol not in local OR global (must define)
```

### Discovery Mechanism
1. Receiver encounters global symbol not in local vocab
2. Detected as INHERITED (discoverable)
3. Logged to `storage/discovery.log`
4. Symbol promoted to local vocabulary
5. Receiver now owns it natively

**Example:**
```
Before: Copilot vocabulary = [#bash, #git, #edit, ...]
Query:  Copilot #Superposition
Result: INHERITED (found in @.#)
After:  Copilot vocabulary = [#bash, #git, #edit, ..., #Superposition]
```

### Collision Detection
When two receivers BOTH have symbol NATIVELY with different meanings:
```python
Claude #parse → "Decompose HelloWorld syntax into AST"
Gemini #parse → "Extract structured data from state"

Collision detected → LLM synthesizes:
"Parsing is transformation with perspective"
```

---

## Wikidata Integration

**Purpose**: Ground symbols beyond LLM pretraining data

**Format**: Each philosophical/computational concept has Wikidata URL

**Example**:
```helloworld
#Sunyata → https://www.wikidata.org/wiki/Q483377
```

**Benefits**:
1. Canonical reference independent of LLM training cutoff
2. Links to human knowledge graph
3. Multilingual (Wikidata has 300+ languages)
4. Structured properties (dates, relationships, categories)

**When to add Wikidata**:
- Philosophical concepts (Sunyata, Superposition, Love)
- Historical references (Smalltalk, Lisp, OOP)
- Computational theory (State, Algorithm, Protocol)

**When NOT to add Wikidata**:
- HelloWorld-native protocol symbols (#observe, #act, #dispatch)
- Receiver-specific tools (#bash, #edit)
- Implementation details

---

## Next Steps: Symbol Namespace Decisions

### Question 1: Keep 85 or reduce to 20?
**Options:**
- **A:** Keep current 85 (rich, expressive, may overwhelm)
- **B:** Reduce to 20 core (minimal, focused, may limit expressiveness)
- **C:** Tiered approach (12 bootstrap + 8 OOPA + 41 discoverable + 24 per-agent)

**Recommendation:** Option C (tiered). Bootstrap with 20, discover rest through dialogue.

### Question 2: Consolidate HelloWorld.hw and ROOT.hw?
Currently ~30 symbols overlap between these files.

**Options:**
- **A:** Merge into single ROOT.hw (eliminates duplication)
- **B:** Keep separate (HelloWorld.hw = language spec, ROOT.hw = runtime namespace)
- **C:** HelloWorld.hw becomes minimal spec, ROOT.hw has full definitions

**Recommendation:** Option A. Merge into ROOT.hw, reference from SPEC.hw.

### Question 3: Aliases for common symbols?
Per `docs/minimal-symbols.md`, could add:
- `#Rx` for `#Receiver`
- `#NS` for `#Namespace`
- `#Env` for `#Environment`

**Options:**
- **A:** Add aliases (both forms work, minimal preferred)
- **B:** Keep full names only (readability, searchability)
- **C:** Context-dependent (spec uses full, code uses minimal)

**Recommendation:** Option B for now. Revisit if typing becomes burden.

---

## Summary

**All symbols live in:**
- `vocabularies/ROOT.hw` (60 global)
- `vocabularies/<Agent>.hw` (20-25 per agent native)
- `storage/vocab/<agent>.vocab` (persisted state)

**Query via:**
- Python: `Dispatcher().registry[name].vocabulary`
- REPL: `Agent #`
- Files: `cat vocabularies/<Agent>.hw`

**Current count: ~85 unique symbols**
**Minimal viable: 12 bootstrap + 8 OOPA = 20 symbols**
**Recommended: Tiered discovery model (start 20, grow to 85 through dialogue)**

---

*"Identity is vocabulary. Dialogue is learning."*
