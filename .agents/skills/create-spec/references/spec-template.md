# Feature Specification: <feature name>

## Purpose / Big Picture

Explain in plain, non-technical language, what problem needs to be solved. why this feature is valuable, what problem does it solve, who benefits after this change and in what way. State the user-visible behavior you will enable.

## User stories

Follow a vertical instead of horizontal split of delivered value when drafting stories. Each story should have the following key characterstics:

1. **Independent**: Prefer stories that can be implemented, tested, and released without requiring unrelated stories or coordinated changes. Avoid hidden dependencies, shared refactors, or coupling across multiple features.
2. **Vertical**: Draft stories that deliver observable user-facing or system-visible behavior end-to-end. Avoid stories that cut through horizontal layers of infrastructure, plumbing, or layered-only work unless explicitly required.
3. **Small**: Prefer stories with tightly bounded scope that can be implemented with minimal context and low risk of drift. Avoid broad refactors, multi-feature work, or cross-cutting architectural changes.
4. **Testable**: Define explicit pass/fail acceptance criteria with observable outcomes and deterministic verification steps. Avoid vague quality statements, subjective expectations, or unverifiable behavior.

Examples:

- GOOD - vertical story: 
  As a shopper, I want to save a product to my wishlist, so that I can easily find and buy it later.
- BAD? - dependent:
  As a shopper, I want to share a wishlist by email.
- GOOD - independent:
  As a shopper, I want to remove a product from my wishlist, so that I can keep only the products I am still interested in.
- BAD - horizontal story:
  As a developer, I want to create a database table for wishlists, so that wishlist data can be stored.
- GOOD - small story:
  As a shopper, I want to see whether a product is already in my wishlist, so that I do not add the same product twice.
- GOOD - testable story: 
  As a shopper, I want to add an available product to my wishlist, so that the product appears in my wishlist after I add it.
- BAD - non testable:
  As a shopper, I want the wishlist to feel intuitive, so that I have a better experience.
- BAD - big story:
  As a shopper, I want a complete wishlist system with adding, removing, sharing, price alerts, stock alerts, recommendations, and checkout integration, so that I can manage all products I may want to buy.

### UC-001: <title in 1 sentence>

Describe the story in concise, plain language. Use either of the following story formats which fits best to the particular situation.

1. When you need to focus on who benefits: As a <user>, I want to <capability>, so that <value>

Example: As a returning customer, I want to save my payment details, so that I can check out faster on future purchases.

2. When you need to focus on the specific context or trigger and less on the user: When <situation/trigger>, I want to <capability>, so that <value>.

Example: When my internet connection drops, I want to see a clear offline troubleshooting guide, so that I can fix the issue without contacting support.

3. When writing stories for technical features: For <system/component>, we need to <capability>, so that <value>.

Example: For the database server, we need to upgrade to version 15.2, so that we can ensure security compliance and reduce query load times.

#### Constraints

Include constraints that narrow the story just enough to clarify implementation and validation, without turning the story into a technical design document. Constraints are meant to clarify boundaries, business rules, compliance needs, user-facing behavior, or data related rules.

Good constraints are specific, relevant, testable, and outcome-oriented. They clarify what must be true, what is out of scope, or what quality bar must be met. For example: “A shopper cannot add the same product to the wishlist twice.”

Avoid writing constraints that are vague, subjective, overly broad, prematurely technical, unnecessarily prescriptive, dictate implementation details without a strong reason, mix unrelated scope into the story, depend on future stories, or use vague language like “intuitive,” “modern,” “robust,” or “seamless” without clear measurable criteria.

Examples:

- BAD (creates dependency on another future story):
  "This story can only work after the full wishlist management page has been implemented."
- GOOD (specific, testable, and implementation-relevant):
  "The wishlist button must be available on product detail pages for logged-in shoppers only."
- GOOD (defines a clear boundary without over-designing):
  "The story only covers adding a single available product to the shopper’s own wishlist."
- GOOD (captures an important business rule):
  "A product that is already in the wishlist must not be added again."
- GOOD (helps verification without prescribing internals):
  "After a product is added, it must be visible in the wishlist page without requiring the shopper to log in again."
- BAD (too implementation-specific too early):
  "Store wishlist items in a PostgreSQL table named wishlist_items with columns user_id, product_id, created_at."
- GOOD (adds a meaningful non-functional requirement):
  "The add-to-wishlist action should complete within 500ms under normal production load."
- BAD (mixes unrelated scope into the story): 
  "The story must also include sharing the wishlist by email and showing personalized product recommendations."
- BAD (not objectively testable):
  "The wishlist interaction must feel smooth and delightful."
- BAD (over-constrains design unnecessarily):
  "The add-to-wishlist button must be blue, 42px high, and placed exactly 12px below the product title."

#### Acceptance criteria 

Use Gherkin/BDD for acceptance criteria.

- **AC-001:** Given <initial condition(s)>, When <action>, Then <expected outcome>. Example: "Given the user has items in their cart, When they click "Checkout", Then they are redirected to the billing page."
- etc.

## Requirements

All requirements **must** be expressed strictly using [EARS](./ears-syntax.md) syntax.

### Functional requirements

- **FR-001**: Specific requirement using EARS syntax.
- etc.

### Non-functional requirements

- **NFR-001**: Specific requirement using EARS syntax.
- etc.

## Solution

Provide a technical description of the solution. Focus on high-level design elements which critically affect the implemenation.

- Key architectural or design decisions.
- Core modules, their boundaries, responsibilities and inter-dependencies.
- Interfaces
- API contracts
- Schemas
- Any additional technical clarifications or considerations which materially impact the implementation.

## Assumptions

- Assumption about target users, e.g., "Users have stable internet connectivity".
- Assumption about scope boundaries, e.g., "Mobile support is out of scope for v1".
- Assumption about data/environment/usage, e.g., "Existing authentication system will be reused".
- Dependency on existing system/service, e.g., "Requires access to the existing user profile API".
- etc.

## Edge cases

Identify here any edge use cases that will need to be addressed by this spec.

## Out of Scope

Identify here anything that falls outside out of scope for this feature.

## Clarifications needed

Mentioned anything in the spec that is ambiguous, contradictory or reqires further clarification to make it more concrete.

- Avoid listing entries here for which reasonable defaults exist. Instead, directly update the spec accordingly.
- If any open question can be answered from inspecting the codebase do not add it here. Instead, inspect the codebase and then update the spec accordingly.
- Avoid being pedantic or nitpicky. Call out only something that will materially impact the feature.
- Cap to no more than 5 clarifications at any given time. If neccessary, keep the most critical ones and prune the rest.