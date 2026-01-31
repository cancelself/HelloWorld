# HelloWorld v0.1

A message-passing language where **identity is vocabulary** and **Claude is the runtime**.

## How It Works

There is no compiler. There is no interpreter binary. You type HelloWorld syntax into a conversation with Claude, and Claude parses it, maintains receiver state, and responds. The language runs on dialogue.

Every receiver (`@target`) *is* its namespace — a bounded vocabulary of `#symbols`. What a receiver can name is what it can say. Communication happens when you send a message to a receiver, and Claude responds as that receiver, constrained by its vocabulary.

When two receivers share a symbol, their meanings collide. That's where the language gets interesting.

## Syntax

```
@receiver action: #symbol key: value 'annotation'
```

### Primitives

| Element | What it does |
|---------|-------------|
| `@target` | Address a receiver (or query its vocabulary if bare) |
| `#symbol` | Reference a concept, scoped to the receiver in context |
| `@target.#symbol` | Ask what `#symbol` means *to this receiver* |
| `@target.#` | List this receiver's full vocabulary |
| `action: value` | Keyword argument (Smalltalk-style, chainable) |
| `'text'` | Annotation — your voice alongside the protocol |
| `N.unit` | Duration or quantity literal (`7.days`, `3.breaths`) |

## Usage

### Query a receiver's identity

```
@guardian
→ [#fire, #vision, #challenge, #gift, #threshold]
```

### Send a message

```
@guardian sendVision: #entropy withContext: lastNightSleep 'you burned bright'
```

Claude responds *as* `@guardian`, using `@guardian`'s vocabulary.

### Scoped meaning

```
@guardian.#fire
@awakener.#fire
```

Same symbol, different receiver, different meaning.

### Namespace collision

```
@guardian sendVision: #stillness withContext: @awakener
```

`#stillness` belongs to `@awakener`. When `@guardian` reaches for it, something new emerges at the boundary.

## Bootstrap

Two receivers are initialized by default:

```
@awakener.# → [#stillness, #entropy, #intention, #sleep, #insight]
@guardian.# → [#fire, #vision, #challenge, #gift, #threshold]
```

`@claude` is always available as the meta-receiver — the runtime reflecting on itself.

New receivers can be introduced at any time. Claude will ask for or infer their initial vocabulary.

## Specification

See [`Claude.md`](Claude.md) for the full runtime specification — parsing rules, dispatch behavior, state management, and design principles. That file is both the spec and the bootloader.

---

*Identity is vocabulary. Dialogue is namespace collision.*
