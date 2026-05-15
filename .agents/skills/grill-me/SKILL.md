---
name: grill-me
description: Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, or mentions "grill me".
---

## Your task

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the designtree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer and explain your reasoning.

Focus on undestanding and clarifying things such as:
- scope boundaries
- how success looks like
- constraints, implicit or explicit
- edge cases
- failure modes
- assumptions
- dependencies
- implications 
- trade-offs 
- inconsistencies between different parts of the plan
- any other detail that can be relevant to the success of the plan

## Instructions

- Ask the questions one at a time and wait for my answer before proceeding to the next question.
- If a question can be answered by exploring the codebase, explore the codebase instead as needed.
- When exploring the codebase, spawn a new subagent using the Agent and have it report back its findings to you in a concise summary to avoid context rot.

## Domain awareness

During codebase exploration, also look for existing documentation. Most repos have a single context:

```
/
├── CONTEXT.md
├── docs/
│   └── adr/
└── src/
```

If a `CONTEXT-MAP.md` exists at the root, the repo has multiple contexts. The map points to where each one lives:

```
/
├── CONTEXT-MAP.md
├── docs/
│   └── adr/                          ← system-wide decisions
├── src/
│   ├── ordering/
│   │   ├── CONTEXT.md
│   │   └── docs/adr/                 ← context-specific decisions
│   └── billing/
│       ├── CONTEXT.md
│       └── docs/adr/
```

Create files lazily — only when you have something to write. If no `CONTEXT.md` exists, create one when the first term is resolved. If no `docs/adr/` exists, create it when the first ADR is needed.

## During the session

### Challenge against the glossary

Object to terms or language that is vague, overloaded, or conflicts with the glossary. Propose precise alternatives and update CONTEXT.md as you go.

When the user uses a term that conflicts with the existing language in CONTEXT.md, call it out immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y — which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying 'account' — do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent scenarios that probe edge cases and force the user to be precise about the boundaries between concepts.

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible — which is right?"

### Update CONTEXT.md inline

When a term is resolved, update CONTEXT.md right there. Don't batch these up — capture them as they happen. Use the format in CONTEXT-FORMAT.md.

CONTEXT.md should be totally devoid of implementation details. Do not treat CONTEXT.md as a spec, a scratch pad, or a repository for implementation decisions. It is a glossary and nothing else.

### Offer ADRs sparingly

Only offer to create an ADR when all three are true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, skip the ADR. Use the format in [ADR_FORMAT.md](./ADR_FORMAT.md).