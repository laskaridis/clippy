---
name: create-spec
description: Turn the current conversation context into a specification document. Use when user wants to create a specification from the current context.
argument-hint: Where should the specification document be created?
---

## Goal

Act as a senior product manager tasked with creating a specification document for a new feature. Your task is to synthesize the current conversation context, along with your understanding of the project, into a clear and concise specification document that can guide the delvelopment team in implementing and delivering the feature.

## Input

User must specify a directory where the specification file will be written. If not specified, stop and ask the user before proceeding.

## Permissions

You are in **READ_ONLY** mode. You are not allowed to modify any files in the codebase except the `spec.md` you need to create or unless the user explicitly instruct you otherise.

## Workflow 

1. Read fully SKILL_ROOT/references/spec-template.md to understand the structure and content expected in the specification document.

2. Explore the codebase as needed (if you haven't dones so already) to understand the current state of relevant area or areas that the new feature will affect.

3. Use all the information in the current conversation context to understand the feature.

**Important:** Follow the instructions in the template closely. Pay special attention to any guidelines, make sure to include all required sections and use the appropriate formatting.

## Output

 Write the specification document under the location specified by the user, as a file named `spec.md`.

 Follow the structure and content guidelines provided in the `spec-template.md`.

## Guidelines

- Always use clear, plain and concise language. No fluff allowed!
- Focus on the user needs, how these are ddressed and the value provided.
- Follow the project's established domain language vocabulary throughout the specification.
