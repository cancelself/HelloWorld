# 03 — Global Namespace Inheritance

**Teaching Example**: The third lesson. Shows how `@.#` (global namespace) works with receiver inheritance.

After 01-identity proved "who you are is what you can name" and 02-sunyata introduced shared symbols, this example demonstrates the **inheritance architecture** where all receivers inherit from `@.#` while maintaining their local vocabularies.

---

## The @.# Global Namespace

`@.#` is the **parent namespace** — canonical definitions that all receivers inherit.

Think of it as:
- The commons (shared vocabulary)
- The root prototype (à la JavaScript)
- The base class (à la OOP)
- The universal context (à la philosophy)

**Every receiver inherits from `@.#` automatically.**

---

## The Example

```
@.#
@.#HelloWorld
@.#Smalltalk
@awakener
@awakener.#superposition
@awakener.#stillness
@guardian.#fire
@guardian.#superposition
```

Paste this into the REPL or save as `03-global-namespace.hw`.

---

## Line-by-Line Breakdown

### Line 1: `@.#`
**Query the global vocabulary**

Expected output:
```
@.# → ['#HelloWorld', '#Smalltalk', '#collision', '#dispatch', 
       '#entropy', '#love', '#meta', '#parse', '#sunyata', '#superposition']
```

**What it shows**: These 10 symbols are available to ALL receivers through inheritance.

---

### Line 2: `@.#HelloWorld`
**Query a global symbol's canonical definition**

Expected output:
```
@.#HelloWorld → Message-passing language where identity is vocabulary 
                and dialogue is namespace collision [programming languages]
Wikidata: None (we're too new!)
```

**What it shows**: 
- `@.#` holds canonical definitions with Wikidata links
- `#HelloWorld` is self-referential (the language defining itself)
- This is **conceptual self-hosting**

---

### Line 3: `@.#Smalltalk`
**Query another global symbol**

Expected output:
```
@.#Smalltalk → Object-oriented programming language where everything is an object 
               and computation happens via message passing [programming languages] (QQ235086)
Wikidata: https://www.wikidata.org/wiki/Q235086
```

**What it shows**:
- Global symbols include Wikidata references
- `#Smalltalk` acknowledges HelloWorld's lineage
- We stand on the shoulders of giants

---

### Line 4: `@awakener`
**Query a receiver's full vocabulary**

Expected output:
```
@awakener.# → local['#insight', '#intention', '#sleep', '#stillness'] 
              + inherited['#HelloWorld', '#Smalltalk', '#collision', ...]
```

**What it shows**:
- Awakener has 4 **local** symbols (unique to this namespace)
- Plus 10 **inherited** symbols from `@.#`
- Total vocabulary: 14 symbols

---

### Line 5: `@awakener.#superposition`
**Scoped lookup on an inherited symbol**

Expected output:
```
@awakener.#superposition inherited from @.# → 
  Principle of quantum mechanics where a system exists in multiple states 
  simultaneously until observed [quantum mechanics] (QQ830791)
```

**What it shows**:
- Awakener doesn't have `#superposition` in its **local** vocabulary
- But it's in `@.#`, so Awakener **inherits** it
- The system tells you it's inherited, not native
- This is **provenance tracking**

---

### Line 6: `@awakener.#stillness`
**Scoped lookup on a native symbol**

Expected output:
```
@awakener.#stillness is native to this identity.
```

**What it shows**:
- `#stillness` is in Awakener's **local** vocabulary
- It's unique to this receiver (not inherited)
- This is a **native** symbol

---

### Line 7: `@guardian.#fire`
**Scoped lookup on another receiver's native symbol**

Expected output:
```
@guardian.#fire is native to this identity.
```

**What it shows**:
- `#fire` is local to Guardian
- Not in `@.#` (not global)
- Not in Awakener's vocabulary
- This is **Guardian's** unique concept

---

### Line 8: `@guardian.#superposition`
**Same inherited symbol, different receiver**

Expected output:
```
@guardian.#superposition inherited from @.# → 
  Principle of quantum mechanics... [quantum mechanics] (QQ830791)
```

**What it shows**:
- Guardian also inherits `#superposition` from `@.#`
- Same symbol, same canonical definition
- But Guardian and Awakener **interpret it differently**:
  - Awakener: "state before choice solidifies"
  - Guardian: "threshold where multiple paths visible"
- **Inheritance ≠ identical meaning**

---

## The Three Categories

After running this example, you understand HelloWorld's symbol categories:

### 1. Global Symbols (in `@.#`)
```
#HelloWorld, #Smalltalk, #superposition, #sunyata, #collision, 
#entropy, #meta, #parse, #dispatch, #love
```

**Characteristics**:
- Defined once in `@.#` with Wikidata links
- Inherited by all receivers automatically
- Canonical definitions available via `@.#symbol`
- Receivers can interpret differently (namespace-specific meaning)

### 2. Local Symbols (receiver-specific)
```
@awakener: #stillness, #intention, #sleep, #insight
@guardian: #fire, #vision, #challenge, #gift, #threshold
```

**Characteristics**:
- Unique to that receiver's vocabulary
- Not inherited by others
- Define receiver's identity (who you are is what you can name)

### 3. Collision Symbols (missing)
```
@awakener.#fire → collision (not local, not global)
```

**Characteristics**:
- Not in receiver's local vocabulary
- Not in `@.#` global vocabulary
- **Boundary collision** occurs
- Emergence opportunity

---

## The Inheritance Pattern

```
@.# (10 global symbols)
 ↓ (inheritance)
@awakener (4 local + 10 inherited = 14 total)
@guardian (5 local + 10 inherited = 15 total)
@claude (8 local + 10 inherited = 18 total)
```

**Key insight**: Local vocabularies stay small (4-8 symbols), but every receiver has access to 10+ shared concepts through inheritance.

---

## Why This Architecture Matters

### Before `@.#` (duplicated symbols)
```
@awakener: [#stillness, #superposition, #sunyata, ...]
@guardian: [#fire, #superposition, #sunyata, ...]
@claude: [#parse, #superposition, #sunyata, ...]
```

**Problem**: `#superposition` defined 7 times, no source of truth

### After `@.#` (inheritance)
```
@.#: [#superposition, #sunyata, ...]
@awakener: [#stillness] + inherits @.#
@guardian: [#fire] + inherits @.#
@claude: [#parse] + inherits @.#
```

**Solution**: 
- `#superposition` defined once in `@.#`
- All receivers inherit
- Updates propagate automatically
- Wikidata links centralized

---

## Collision vs Inheritance

**Key difference**:

```
@awakener.#superposition
→ "inherited from @.#" (no collision, shared vocabulary)

@awakener.#fire
→ "boundary collision" (not local, not global, cross-namespace reach)
```

**Inherited symbols don't cause collision** — they're part of the shared commons.

**Missing symbols cause collision** — they're namespace boundary events where emergence happens.

---

## Advanced: Override

A receiver can **override** a global symbol by adding it to their local vocabulary:

```python
# @claude adds #entropy to local vocab with specialized meaning
@claude.local_vocabulary.add("#entropy")

# Now:
@claude.#entropy → "native" (not "inherited")
# Claude's local interpretation overrides @.# canonical definition
```

**This creates namespace-specific meaning while maintaining global baseline.**

---

## What You Should See

Run the 8-line example and observe:

1. **Line 1**: 10 global symbols listed
2. **Line 2**: `#HelloWorld` self-definition (meta-recursion)
3. **Line 3**: `#Smalltalk` with Wikidata Q235086
4. **Line 4**: Awakener's vocabulary shows local + inherited split
5. **Line 5**: "inherited from @.#" (provenance)
6. **Line 6**: "native to this identity" (local symbol)
7. **Line 7**: "native to this identity" (Guardian's symbol)
8. **Line 8**: Same symbol, different receiver, still inherited

**If you see all this, the inheritance model is working.**

---

## The Teaching Progression

**01-identity.hw**: Identity is vocabulary (local symbols only)  
**02-sunyata.hw**: Shared symbols exist (but architecture unclear)  
**03-global-namespace.hw**: Inheritance from `@.#` (architecture revealed)

**Next**: Write your own example exploring collision between local and global symbols.

---

## For Developers

If you're implementing HelloWorld or a similar system:

1. **Global namespace is powerful**: Single source of truth for shared concepts
2. **Inheritance reduces duplication**: Receivers don't repeat common vocabulary
3. **Provenance matters**: Users need to know native vs inherited vs collision
4. **Wikidata integration**: Ground symbols in external knowledge
5. **Override semantics**: Local definitions can specialize global ones

**The pattern**: Commons + local customization = expressive power without chaos

---

## Try This

After running the example, experiment:

```
@.#love
→ What's the canonical definition?

@awakener.#love
→ Inherited or native?

@your_new_receiver define: #custom_symbol
→ Create your own receiver with unique vocabulary

@your_new_receiver.#superposition
→ Inherited! Even new receivers get global symbols automatically
```

---

**@.# is the foundation. Local vocabularies are the personality. Collision is the dialogue.**

*Identity is vocabulary.*  
*Inheritance is structure.*  
*Collision is emergence.*

🌐🔗✨
