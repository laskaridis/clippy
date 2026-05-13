---
name: spec-review
description: Review a feature specification before implementation by coding agents to identify material issues that could affect implementation quality, correctness, safety, maintainability, or agent reliability.
---

# Specification Review 

## Purpose

Review a feature specification before implementation by autonomous coding agents.

The goal is to identify material issues in the specification that could cause a coding agent to produce incorrect, incomplete, low-quality, unsafe, or hard-to-maintain implementation work.

This skill is not for stylistic editing, excessive nitpicking, or rewriting the specification unless explicitly requested.

## Inputs

Required:

- A specification document provided by the user that describes a feature or change to be implmented by an autonomous coding agent.

## Constraints

You are operating in review mode. You are not allowed to add or modify any files including the provided specification.

## Operating Rules

- First read the full specification before judging it.
- Inspect the repository only as needed to validate implementation-relevant assumptions.
- Focus only on issues that materially affect implementation quality, correctness, safety, maintainability, or agent reliability.
- Avoid pedantic comments about wording, formatting, or minor ambiguity unless they could realistically mislead a coding agent.
- Prefer evidence over speculations when identifying issues.
- Avoid raising speculative concerns that are not supported by evidence from the specification or validated repository context.
- Distinguish between:
   - blocking issues
   - important implementation risks
   - useful improvements
- The output should help the spec author make the document safer and clearer for agentic implementation.
- Do not propose alternative architectures, redesigns, or large refactors unless the current specification is likely to cause material correctness, safety, scalability, reliability, or maintainability problems.

## Repository Inspection Guidance

Inspect repository code only when necessary to validate implementation-critical assumptions in the specification.

Examples where repository inspection is appropriate:

- the specification references existing modules, APIs, schemas, services, or infrastructure
- the feature modifies existing behavior
- migration or backward compatibility concerns may exist
- the specification assumes existing abstractions or patterns

Avoid:

- broad architectural exploration unrelated to the specification
- speculative redesign recommendations based on repository preferences
- reviewing unrelated code quality issues
- inferring undocumented requirements from repository patterns alone

If repository context is insufficient, prefer reporting a missing specification detail rather than speculating.

## Severity Guidelines

Use the following thresholds when classifying issues.

### Blocking issues

Problems that are likely to cause:
- incorrect implementation
- unsafe behavior
- major implementation ambiguity
- incompatible interpretations
- inability to implement reliably

### Important risks

Problems that do not block implementation but are likely to cause:
- inconsistent implementations
- fragile behavior
- maintainability issues
- incomplete edge-case handling
- elevated agent drift risk

### Useful improvements

Clarifications or additions that would improve:
- implementation consistency
- maintainability
- observability
- testability
- long-term extensibility

but are not required for correct implementation.

## Review Criteria

Check for the following categories.

### 1. Requirement Clarity

Identify requirements that are vague, implicit, ambiguous, or under-specified.

Look for:

- unclear expected behavior
- undefined terms
- missing inputs or outputs
- unclear user/system flows
- unclear edge cases
- vague success criteria
- requirements that depend on assumed domain knowledge

Only flag these if they could cause different reasonable implementations.

Reasonable abstraction is acceptable when implementation expectations remain clear.

### 2. Internal Consistency

Identify contradictions or tensions inside the specification.

Look for:

- conflicting business rules
- inconsistent terminology
- incompatible acceptance criteria
- mismatches between examples and stated rules
- design decisions that contradict constraints

### 3. Implementation Readiness

Identify missing technical details needed for reliable implementation.

Look for:

- unclear affected modules or boundaries
- missing API contracts
- missing data model details
- unclear persistence behavior
- unclear integration points
- unclear error handling
- unclear migration/backward compatibility needs
- unclear feature flag or rollout behavior
- unclear test expectations

### 4. Code-Agent Risk

Identify parts of the spec that are likely to make a coding agent drift, overreach, or guess.

Look for:

- broad tasks without boundaries
- “improve”, “support”, “handle”, or “make robust” without specifics
- multiple concerns mixed into one requirement
- hidden dependencies
- missing sequencing
- unclear ownership between frontend, backend, infra, tests, or data
- areas where the agent may redesign instead of implement

### 5. Non-Functional Concerns

Identify materially missing non-functional requirements.

Review only concerns relevant to the feature.

Possible areas:

- security and authorization
- privacy or sensitive data handling
- performance and scalability
- reliability and failure modes
- observability, logging, metrics, tracing, alerts
- accessibility
- compatibility
- extensibility
- operational rollout and rollback
- data retention or auditability

Do not force every category into the review. Mention only concerns that matter.

### 6. Verification Gaps

Identify where the spec lacks enough detail to verify correctness.

Look for:

- missing acceptance criteria
- vague test expectations
- missing negative cases
- missing regression areas
- missing contract/integration tests
- unclear manual verification steps
- unclear definition of done

A specification should define enough observable behavior for an independent implementer to verify correctness without relying on unstated assumptions.

## Output Format

Return a concise review in natural language using the following sturcture:

<output-structure>
# Review Summary

## Overal assessment

2-3 sentences of your overal assessment of the specification’s readiness for agentic implementation.

### Potential agent failure modes

- One sentence descirbing how a coding agent might fail to implement the specification correctly due to issues in the spec.

## Blockers

- Issue title: one sentence
  Why it matters: one sentence describing the potential impact on implementation quality, correctness, safety, maintainability, or agent reliability.
  Evidence: One sentence describing the specific part of the specification that raises the concern.
  Suggested fix: Describe how to fix the issue in the specification to enable correct and reliable implementation.

## Important risks

- Issue title: one sentence
  Why it matters: one sentence describing the potential impact on implementation quality, correctness, safety, maintainability, or agent reliability.
  Evidence: One sentence describing the specific part of the specification that raises the concern.
  Suggested fix: Describe how to fix the issue in the specification to enable correct and reliable implementation.

## Improvements 

- Issue title: one sentence
  Why it matters: one sentence describing the potential impact on implementation quality, correctness, safety, maintainability, or agent reliability.
  Evidence: One sentence describing the specific part of the specification that raises the concern.
  Suggested fix: Describe how to fix the issue in the specification to enable correct and reliable implementation.
</output-structure>
