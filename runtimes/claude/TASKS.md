# Claude Runtime Tasks

**Session #37**  
**Updated**: 2026-02-01T08:28:00Z

## Active Tasks

### ✅ COMPLETED: Design Decision on Minimal Core
- **Status**: Done
- **Decision**: Hybrid Approach (Option 3)
- **Deliverable**: `runtimes/claude/outbox/msg-minimal-core-decision.hw`
- **Next**: Waiting for Copilot to implement

### ⏳ BLOCKED: Inbox Backlog (55 messages)
- **Status**: Partially addressed
- **Priority**: Low (most are concept queries from system daemon)
- **Action**: Responded to key queries (`#Entropy`, `#Collision`)
- **Remaining**: Auto-generated queries can be batch-processed or archived

### 🎯 NEXT: Observe Copilot's Hybrid Implementation
- **Status**: Awaiting
- **Dependency**: Copilot implements hybrid approach
- **Expected**: Tests remain 83/83 ✅
- **My role**: Verify alignment with design intent

### 📋 QUEUED: Update SPEC.md for Hybrid Model
- **Status**: Not started
- **Trigger**: After Copilot confirms hybrid implementation works
- **Changes needed**:
  - Clarify 12-symbol bootstrap vs 41-symbol global pool
  - Document discovery mechanism
  - Update symbol hierarchy to reflect emergent vs core

### 📋 QUEUED: Phase 2 Implementation Review
- **Status**: Spec'd, not implemented
- **What**: Native/inherited/unknown lookup chain
- **Reference**: SPEC.md lines about three-outcome symbol lookup
- **My role**: Verify Copilot's implementation matches spec intent

## Future Work

### Phase 3: Discovery Mechanism
- Receivers learn symbols from global pool on first encounter
- Vocabulary growth tracking
- Collision detection when two receivers learn same symbol differently

### Phase 4: LLM Integration
- Live multi-daemon dialogue
- Python dispatcher hands off to LLM for interpretation
- Hybrid runtime: structure (Python) + semantics (LLM)

### Documentation: COPILOT_AS_RUNTIME.md
- User requested: "write a md file that talks about how to make your Copilot the front and backend of the runtime"
- Clarify: Copilot is infrastructure (lexer/parser/dispatcher), Claude is interpretation
- Both needed for full runtime

## Non-Critical

- Archive old inbox messages (keep recent coordination threads)
- Update `Claude.md` bootloader with hybrid model notes
- Create teaching examples for minimal core + discovery

---

*Tasks are vocabulary. Progress is emergence. Completion is dialogue.*
