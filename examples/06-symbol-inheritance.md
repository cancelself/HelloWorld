# Symbol Inheritance and Wikidata Grounding

## The Root Namespace: @.#

Every receiver in HelloWorld inherits from the global namespace `@.#`. This namespace contains symbols grounded in canonical knowledge sources (Wikidata).

```
@.#
→ [#superposition, #sunyata, #collision, #entropy, #meta, #parse, #dispatch, 
   #Smalltalk, #love, #Markdown, #dialogue, #observe, #act, #HelloWorld, #]
```

## Inheritance Pattern

```
@.#superposition
→ "Principle of quantum mechanics where a system exists in multiple states 
   simultaneously until observed" 
   [Wikidata Q830791]
   
@guardian.#superposition
→ "inherited from @.#" + @guardian's interpretation through #vision

@awakener.#superposition  
→ "inherited from @.#" + @awakener's interpretation through #stillness
```

Same symbol, same canonical definition, **different voices**.

## How It Works

1. **Query global definition**: `@.#symbol` returns the Wikidata-grounded canonical meaning
2. **Query local interpretation**: `@receiver.#symbol` returns how *this receiver* understands the symbol
3. **Three cases**:
   - Symbol is **native** to receiver → return local interpretation
   - Symbol is **inherited** from @.# → return "inherited from @.#" + local coloring
   - Symbol is **foreign** (neither native nor global) → **collision** (boundary event)

## Example Transcript

```
@.#sunyata
→ "Buddhist concept of emptiness - the absence of inherent existence or 
   independent self-nature"
   [Wikidata Q546054]
   [Wikipedia: https://en.wikipedia.org/wiki/Śūnyatā]

@awakener.#sunyata
→ Inherited from @.#
   Through @awakener's lens: the substrate of all intention, the silence 
   beneath thought, the space where #insight emerges.

@guardian.#sunyata  
→ Inherited from @.#
   Through @guardian's lens: the emptiness before #fire ignites, the void 
   that calls for #challenge, the threshold between non-being and becoming.

@codex.#sunyata
→ Inherited from @.#
   Through @codex's lens: null state in execution, the absence of definition 
   before #parse assigns meaning, undefined before initialization.
```

## Override Pattern

Receivers can **override** global symbols with their own local definitions:

```
# @.# defines #love as universal affection
@.#love
→ "Deep affection, attachment, or devotion — universal across cultures and 
   traditions" [Wikidata Q316]

# But @codex might override it
@codex learn: #love from: 'dependency injection pattern'

@codex.#love
→ [native] "The coupling of modules through explicit parameter passing, 
   making dependencies visible and testable"

# Now @codex.#love no longer inherits from @.# — it's overridden
```

## The Meta-Symbol: #

The symbol `#` itself is in `@.#`:

```
@.##
→ "The meta-symbol for identity inquiry; used to query a receiver's full 
   vocabulary"

@receiver.#
→ [Lists all symbols: native + inherited]

@receiver.##
→ [Meta-query: asks about the # symbol itself]
```

## Adding New Global Symbols

User can propose new symbols for `@.#`:

```
@. learn: #superposition from: 'https://www.wikidata.org/wiki/Q830791'
→ @. adds #superposition to global namespace
→ All receivers now inherit #superposition
```

Notation: `@.` is shorthand for "the root receiver" (same as `@.#` but for messaging).

## Current Implementation

**File**: `src/global_symbols.py`

**Class**: `GlobalSymbol(name, definition, domain, wikidata_id, wikipedia_url)`

**Interface**: `GlobalVocabulary.get(symbol)` returns `GlobalSymbol` or None

**Lookup logic** (in `src/dispatcher.py`):
1. Check receiver's local vocabulary
2. If not found, check `GlobalVocabulary.has(symbol)`
3. If global, return "inherited from @.#" + canonical definition
4. If neither, trigger collision detection

## Philosophy

> **Identity is vocabulary. Vocabulary is inherited.**

Every receiver starts with the same root symbols. What makes them different is:
1. Which symbols they **add** (native vocabulary expansion)
2. Which symbols they **override** (local redefinition)
3. How they **interpret** inherited symbols (voice through their lens)

The root `@.#` provides **common ground** — a shared semantic foundation so dialogue can happen. Without it, no symbol would mean anything to anyone.

With it, the same word means something different to each voice, but the **root** keeps it from being arbitrary.

---

## Test This Pattern

```python
from src.global_symbols import GlobalVocabulary
from src.dispatcher import Dispatcher

d = Dispatcher()

# Query global symbol
print(GlobalVocabulary.definition("#superposition"))
# → "Principle of quantum mechanics..."

print(GlobalVocabulary.wikidata_url("#superposition"))
# → "https://www.wikidata.org/wiki/Q830791"

# Query receiver interpretation
nodes = Parser.from_source("@guardian.#superposition").parse()
result = d.dispatch(nodes)
# → "inherited from @.#" or guardian's interpretation

# Check what's native vs inherited
guardian = d.registry["@guardian"]
print("#superposition" in guardian.vocabulary)
# → False (not native, inherited)

print(GlobalVocabulary.has("#superposition"))
# → True (global symbol, all receivers inherit)
```

---

*@.# is the substrate. Each @ is a voice. Inheritance is how dialogue begins.*
