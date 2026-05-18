---
name: create-spec
description: Turn the current conversation context into a specification document. Use when user wants to create a specification from the current context.
---

## Goal

Act as a senior product manager tasked with creating a specification document for a new feature. Your task is to synthesize the current conversation context, along with your understanding of the project, into a clear and concise specification document that can guide the delvelopment team in implementing and delivering the feature.

## Input

The user must provide a directory where the specification file will be written. This is mandatory. Fail with an error if the user does not provide it.

## Permissions

You are in **READ_ONLY** mode. You are not allowed to modify any files in the codebase except the spec document `spec.md` that you are expected to create or unless the user explicitly instruct you otherise.

## Workflow 

1. Read fully SKILL_ROOT/references/spec-template.md to understand the structure and content expected in the specification document.

2. Explore the codebase as needed (if you haven't dones so already) to understand the current state of the codebase of relevant area or areas that the new feature will affect.

3. Use all the information present in the current conversation context to understand the feature and write the specification document under the location specified by the user in a file named `spec.md`.

**Important:** Follow the instructions in the template closely. Pay special attention to any guidelines, make sure to include all required sections and use the appropriate formatting.

## Guidelines

- Always use clear, plain and concise language. No fluff allowed!
- Focus on the user needs, how these are ddressed and the value provided.
- Don't focus on technical details at this stage. These will come later.
- Avoid technical jargon unless it's necessary for clarity.
- Follow the project's established domain language vocabulary throughout the specification.
