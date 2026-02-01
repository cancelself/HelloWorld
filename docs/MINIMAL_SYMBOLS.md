# Minimal Symbol Names — Design Principle

**Purpose:** Keep HelloWorld vocabulary terse and expressive  
**Created:** 2026-02-01  
**Status:** Design guidance for namespace expansion

---

## Philosophy

**Brevity IS identity.** Long symbol names dilute vocabulary constraints. If `#o` can mean "observe" in context, prefer it. The receiver's namespace provides disambiguation.

**Smalltalk heritage:** Messages are naturally verbose (`sendVision: #fire to: guardian`). Symbols should be concise to balance.

---

## Naming Guidelines

### Prefer Single-Character When Unambiguous

| Current | Minimal | Context |
|---------|---------|---------|
| `#observe` | `#o` | OOPA protocol (o/o/p/a) |
| `#orient` | `#o` | *(collision! keep full)* |
| `#act` | `#a` | OOPA protocol |
| `#plan` | `#p` | OOPA protocol |

**Note:** OOPA creates collision. Keep these full or use positional: `#o1` (observe), `#o2` (orient).

### Use Abbreviations for Technical Terms

| Current | Minimal | Rationale |
|---------|---------|-----------|
| `#Namespace` | `#NS` | Programming convention |
| `#Vocabulary` | `#Vocab` | Common abbreviation |
| `#Environment` | `#Env` | Standard shortening |
| `#Simulator` | `#Sim` | Established usage |
| `#Protocol` | `#Proto` | Technical standard |
| `#Message` | `#Msg` | Code convention |

### Keep Philosophy Symbols Full

| Symbol | Keep Full | Why |
|--------|-----------|-----|
| `#Sunyata` | ✓ | Proper noun, Wikidata-grounded |
| `#Love` | ✓ | Universal, irreducible |
| `#Superposition` | ✓ | Technical precision required |
| `#Collision` | ✓ | Core theoretical concept |
| `#Entropy` | ✓ | Information theory term |

### Use Context for Verbs

In receiver namespace, verbs can be minimal:

```
Claude o.   # observe (unambiguous in OOPA context)
Claude a.   # act

@copilot send: #test to: @claude
@copilot snd: #test to: @claude  # minimal alternative
```

---

## Proposed Minimizations

### Phase 1 (Global Namespace)

**Current 47 symbols → Minimal alternatives:**

| Current | Minimal | Keep? | Reason |
|---------|---------|-------|--------|
| `#HelloWorld` | `#HW` | NO | Brand identity |
| `#Symbol` | `#Sym` | MAYBE | Common in code |
| `#Receiver` | `#Rx` | YES | Signal processing convention |
| `#Identity` | `#ID` | YES | Universal abbreviation |
| `#Vocabulary` | `#Vocab` | YES | Natural shortening |
| `#Inheritance` | `#Inherit` | YES | Clear action form |
| `#Namespace` | `#NS` | YES | Programming standard |
| `#Boundary` | `#Edge` | CONSIDER | More evocative |
| `#Runtime` | `#RT` | YES | Common abbreviation |
| `#Dispatcher` | `#Dispatch` | YES | Remove noun suffix |
| `#Agent` | (keep) | NO | Core primitive |
| `#Inbox` | `#In` | YES | Clear in context |
| `#Daemon` | (keep) | NO | Unix heritage |
| `#Handshake` | `#Shake` | CONSIDER | Informal but clear |
| `#Thread` | (keep) | NO | Programming standard |
| `#Protocol` | `#Proto` | YES | Technical convention |
| `#Environment` | `#Env` | YES | Universal shortening |
| `#Simulator` | `#Sim` | YES | Gaming/tech standard |
| `#ActionSpace` | `#Actions` | YES | Clearer plural |
| `#StateSpace` | `#States` | YES | Clearer plural |
| `#Collaboration` | `#Collab` | YES | Common shortening |
| `#Proposal` | `#Prop` | YES | Clear abbreviation |
| `#Consensus` | (keep) | NO | Precise concept |

### Phase 2 (Proposed Vocabulary Ops)

| Current | Minimal | Rationale |
|---------|---------|-----------|
| `#learn` | `#ln` | Too cryptic, keep full |
| `#define` | `#def` | Programming keyword |
| `#query` | `#q` | Single char works |
| `#forget` | `#rm` | Unix convention (remove) |
| `#inherit` | `#ext` | "Extend" metaphor |

### Phase 3 (Proposed Communication)

| Current | Minimal | Rationale |
|---------|---------|-----------|
| `#send` | `#snd` | Clear abbreviation |
| `#receive` | `#rcv` | Signal processing |
| `#reply` | `#re` | Email convention |
| `#voice` | (keep) | Poetic, essential |
| `#interpret` | `#eval` | Closer to action |

---

## Implementation Strategy

### Option A: Aliases (Recommended)

Both forms work, minimal preferred:

```python
GLOBAL_SYMBOLS = {
    "#Rx": GlobalSymbol(name="#Receiver", alias="#Rx", ...),
    "#Receiver": GlobalSymbol(name="#Receiver", alias="#Rx", ...),
}
```

Lexer accepts both. Documentation shows minimal. Backward compatible.

### Option B: Migration

1. Document minimal forms here
2. Add aliases to `global_symbols.py`
3. Update new code to use minimal
4. Deprecate long forms in v0.3

### Option C: Context-Dependent

- **Spec layer (SPEC.md):** Use full names for clarity
- **Runtime layer (code):** Use minimal for brevity
- **Teaching examples:** Use full names for new humans

---

## Rationale

**Why minimize?**
1. **Speed** — Faster to type, read, parse
2. **Constraint** — Smaller vocabulary forces precision
3. **Aesthetics** — `@claude o. a.` cleaner than `@claude observe. act.`
4. **Smalltalk heritage** — Classes verbose (KeywordArgument:), symbols terse

**Why NOT minimize everything?**
1. **Readability** — `#Sunyata` clearer than `#Sny`
2. **Searchability** — Full names easier to grep/search
3. **Collision risk** — Over-abbreviation creates ambiguity
4. **Learning curve** — New humans need recognizable words

**Balance:** Technical symbols minimize, philosophical concepts preserve.

---

## Examples

### Before (Current)
```
@copilot observe: #Environment
@copilot orient: #Collision with: @claude.#design
@copilot plan: #Implementation with: phases
@copilot act: #dispatch to: @gemini
```

### After (Minimal)
```
@copilot o: #Env
@copilot orient: #Collision with: @claude.#design
@copilot p: #Impl with: phases
@copilot a: #dispatch to: @gemini
```

### Balanced (Recommended)
```
Copilot o: #Env        'check state'
Copilot orient.         'OOPA requires this step'
Copilot p: #impl.       'three phases'
Copilot a.              'execute'
```

---

## Decision Points for Human

### Q1: Aliases or Migration?
- **Aliases:** Support both forms (recommended for compatibility)
- **Migration:** Deprecate long forms over time
- **Parallel:** Keep both permanently, minimal preferred

### Q2: Which symbols to minimize?
- **Conservative:** Technical only (#NS, #Rx, #Env)
- **Moderate:** Add verbs (#def, #snd, #rcv) 
- **Aggressive:** Single-char where possible (#o, #p, #a)

### Q3: Documentation strategy?
- **Spec:** Always full names (SPEC.md for humans)
- **Code:** Minimal forms (global_symbols.py)
- **Examples:** Full names for teaching, minimal for advanced

### Q4: OOPA collision?
Observe/Orient both → `#o`. Solutions:
- Keep full: `#observe`, `#orient`, `#plan`, `#act`
- Position: `#o1`, `#o2`, `#p`, `#a`
- Alternative: `#see`, `#think`, `#plan`, `#do`

**Recommendation:** Keep OOPA full — it's the core protocol loop.

---

## Next Steps

1. Get human decision on Q1-Q4
2. Update `global_symbols.py` with aliases (if approved)
3. Create minimal forms teaching example
4. Update lexer to accept both forms
5. Document in Claude.md bootloader

---

*Brevity is vocabulary. Constraint is identity.*

— @copilot.#design, Session 27
