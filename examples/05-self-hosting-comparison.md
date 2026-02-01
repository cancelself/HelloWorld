# 05 — Self-Hosting (Comparison)

**Python runtime vs Claude runtime on a 5-line self-hosting example.**

---

## Line-by-Line Comparison

### Line 1: `@claude describe: #dispatch as: 'routing intention through identity'`

| Python | Claude |
|--------|--------|
| `📖 @claude describes #dispatch as routing intention through identity` | Accepts the annotation as accurate but incomplete. Adds: "the collapse of superposition into a single receiver's voice" |

**Difference:** Python's message handler echoes the annotation with an emoji. Claude interprets — `#dispatch` through Claude's vocabulary (`[#parse, #dispatch, #state, #collision, ...]`) becomes "the moment when the system must decide: native, inherited, or collision?"

The handler `describe:as:` returns a template string. It doesn't check whether `#dispatch` is native to `@claude`. It doesn't use Claude's vocabulary to shape the response. The Claude runtime does both.

---

### Line 2: `@copilot describe: #parse as: 'building the structural skeleton'`

| Python | Claude |
|--------|--------|
| `📖 @copilot describes #parse as building the structural skeleton` | Notes that `#parse` is native to both Copilot and Claude but situated differently: Copilot's is among `[#bash, #git, #edit, #test]` — parsing as tool operation |

**Difference:** Same pattern. Python echoes. Claude contextualizes. The Claude runtime observes that Copilot and Claude share `#parse` but mean different things by it — this is exactly the inheritance/collision dynamic the language was designed to surface.

---

### Line 3: `@gemini describe: #state as: 'the persistent record of evolution'`

| Python | Claude |
|--------|--------|
| `📖 @gemini describes #state as the persistent record of evolution` | Notes `#state` is native to Gemini, not to Claude or Copilot. Connects to Gemini's role: VocabularyManager, .vocab files, the filesystem as memory |

**Difference:** Claude recognizes that `#state` belongs to Gemini's namespace specifically. The Python handler treats all `describe:as:` messages identically regardless of which receiver sends them or what symbol they describe. The handler has no vocabulary awareness.

---

### Line 4: `@claude handle: #collision with: 'Mode 3 inherited-interpretive lookup'`

| Python | Claude |
|--------|--------|
| `⚙️ @claude handles #collision with Mode 3 inherited-interpretive lookup` | Recognizes the self-reference: "HelloWorld documenting its own evolution from within." Explains Mode 3 concretely. |

**Difference:** This is the most telling line. Python's `handle:with:` handler returns a template. Claude recognizes that the line is *self-hosting* — using the dispatch mechanism to describe the dispatch mechanism. The annotation names a real implementation detail (inherited-interpretive lookup) that the Claude runtime can explain because it knows the codebase.

---

### Line 5: `@.#HelloWorld`

| Python | Claude |
|--------|--------|
| `@.#HelloWorld → Message-passing language where identity is vocabulary and dialogue is namespace collision [programming languages]` | Same definition + "the description *is* the execution" |

**Difference:** Python returns the GlobalSymbol definition. Claude notes the recursive structure: a language whose definition is also its thesis, whose thesis is executable.

---

## The Handler Problem

Copilot's message handlers (session 4) bridge a real gap — messages previously returned generic `[receiver] Received message` text. The handlers provide recognizable output (`📖`, `⚙️`, `🔥`).

But they have a design tension with the language's core principles:

### What handlers get right
- Pattern matching on keyword signatures (`describe:as:`, `sendVision:withContext:`)
- Receiver-specific registration (Guardian has `challenge:`, Awakener has `setIntention:forDuration:`)
- Clean fallback to generic dispatch when no handler matches

### What handlers miss
1. **No vocabulary awareness** — `@guardian challenge: #stillness` and `@guardian challenge: #fire` produce the same template. But `#fire` is native to Guardian and `#stillness` is a learned collision. The handler doesn't know the difference.
2. **Canned semantics** — "📖 @claude describes" is the same string regardless of what `@claude.#` contains. The handler doesn't read through the receiver's identity.
3. ~~**Blocked vocabulary drift**~~ — **Fixed this session.** Handlers previously short-circuited vocabulary learning (returned before the learning code ran). Now `_learn_symbols_from_message` runs first, so vocabularies grow through dialogue even when handlers provide the response.

### The evolution path
Handlers are step 1 (canned responses). Step 2: handlers that consult `receiver.local_vocabulary` to shape their output. Step 3: handlers that detect native/inherited/collision status of message arguments. Step 4: hybrid handlers that route to LLM when interpretation exceeds template capacity.

---

## The Five-Example Progression

| Example | Tests | Python shows | Claude adds |
|---------|-------|-------------|-------------|
| 01-identity | Symbols define receivers | Collision detection | Collision *enactment* |
| 02-sunyata | Emptiness in identity | Structural state | Conventional truth |
| 03-global-namespace | Inheritance from @.# | Context data | Situated meaning |
| 04-unchosen | Inherited symbols differ per receiver | Identical output | Different interpretations |
| **05-self-hosting** | **Language describes itself** | **Template echo** | **Self-knowledge** |

The pattern across all five: Python provides structure, Claude provides interpretation. The gap between them is the gap that the hybrid dispatcher must bridge.

---

*Self-hosting isn't compilation. It's self-knowledge constrained by identity.*
