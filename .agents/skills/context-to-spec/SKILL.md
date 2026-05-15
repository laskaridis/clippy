---
name: context-to-spec
description: Turn the current conversation context into a specification document. Use when user wants to create a PRD from the current context.
---

Use this skill to create a specification document from the current conversation context and codebase understanding. 

## Input

The user must provide the location of the specification file. This is mandatory. Fail with an error if the user does not provide it.

## Your task

1. Explore the repo to understand the current state of the codebase, if you haven't already. Use the project's domain glossary vocabulary throughout the specification, and respect any design or architectural decisions the area you're touching.

Important: when exploring the codebase spawn a new subagent with clear instruction on what to look for and have it report back to you its findings in a concise manner to avoid context rot.

2. Sketch out the major modules you will need to build or modify to complete the implementation. Actively look for opportunities to extract deep modules that can be tested in isolation.

A deep module (as opposed to a shallow module) is one which encapsulates a lot of functionality in a simple, testable interface which rarely changes.

Check with the user that these modules match their expectations. Check with the user which modules they want tests written for.

## Explected Output

Use docs/PLANS.md to create the specification document in the location specified by the user.
