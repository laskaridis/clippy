# Phase 0 Research: Web Clipping and Reference Application

**Feature**: [specs/001-web-clipping-app/spec.md](specs/001-web-clipping-app/spec.md)  
**Plan**: [specs/001-web-clipping-app/plan.md](specs/001-web-clipping-app/plan.md)  
**Date**: 2026-01-15

This document captures key technical decisions for the MVP, along with rationale and alternatives considered. It resolves initial technical unknowns for the implementation plan.

---

## Runtime and Framework

**Decision**: Use Python 3.11+ (targeting 3.12 where available) with Django 5.2 for a monolithic backend.

**Rationale**:
- Django is already present in the project dependencies and is well-suited to CRUD-style applications with authentication and admin.
- A monolithic Django project aligns with the constitution’s requirement for a simple architecture (extension + backend + DB + web UI) without introducing premature microservices.
- Python 3.11/3.12 provide good performance and are well supported by Django 5.2.

**Alternatives considered**:
- **FastAPI + separate frontend**: More explicit API-first approach, but adds more moving parts (separate frontend stack, more complex deployment) for little MVP benefit.
- **Node.js/Express**: Would introduce a different ecosystem than the existing Python stack and libraries in this repo.

---

## API Style and Contracts

**Decision**: Expose a JSON REST API using Django REST Framework (DRF).

**Rationale**:
- REST/JSON is straightforward for both the Chrome extension and the web application to consume.
- DRF integrates cleanly with Django models, serializers, and authentication, accelerating development.
- REST endpoints map naturally to clippings, labels, and authentication resources.

**Alternatives considered**:
- **GraphQL (e.g., Graphene or Ariadne)**: Flexible queries but adds conceptual and operational complexity that is not necessary for the initial set of simple resources.
- **Plain Django views returning JSON**: Less boilerplate but sacrifices DRF’s built-in validation, browsing, and authentication features.

---

## Storage and Data Model

**Decision**: Use PostgreSQL as the primary datastore, with Django models for User, Clip, and Label.

**Rationale**:
- PostgreSQL is already a dependency and is a strong default for structured text data and indexing.
- Django’s ORM and migrations make it easy to evolve the schema as the product matures.
- Full-text search can be added incrementally (e.g., PostgreSQL tsvector indexes) if needed.

**Alternatives considered**:
- **Document store (e.g., MongoDB)**: More flexible for unstructured data but less aligned with existing dependencies and not necessary for the current, well-structured domain.
- **SQLite-only**: Acceptable for local development but not ideal for cloud-native, multi-instance deployments.

---

## Authentication and Authorization

**Decision**: Use Django’s built-in authentication system (session-based) with per-user scoping of clippings and labels; Chrome extension will rely on the same cookies and CSRF protections as the web app.

**Rationale**:
- Reuses Django’s mature auth system and avoids introducing a separate identity provider for the MVP.
- Fits the constitution’s requirement that clips be private per user and not shared without explicit features.
- For the Chrome extension, the user can sign in via the web UI on the same domain; extension requests will include session cookies for authenticated API calls.

**Alternatives considered**:
- **JWT-based token auth**: More explicit for APIs and third-party clients, but introduces token management, rotation, and associated complexity not critical for an MVP with only a first-party extension.
- **External identity provider (OAuth/OIDC)**: Helpful for enterprise scenarios but overkill for early stages.

---

## Chrome Extension Scope (MVP)

**Decision**: Target Chrome only for capture, focusing on selected-text clipping and lightweight metadata capture.

**Rationale**:
- Aligns with the constitution’s "browser-first" capture principle and user requirement to clip while browsing.
- Limits scope to one browser for the MVP, reducing cross-browser compatibility work.
- Keeps permissions minimal: access to active tab, read page content as needed for selection, and network access to the backend domain.

**Alternatives considered**:
- **Supporting multiple browsers (Edge, Firefox) from day one**: Increases the testing and permissions surface area without immediate value.
- **Full-page screenshot or rich-format clipping**: Adds complexity in storage and rendering and is outside the current text-focused spec.

---

## Cloud-Native Approach

**Decision**: Containerize the Django app and use PostgreSQL as an external service; follow 12-factor principles with configuration via environment variables and stateless application instances.

**Rationale**:
- Containerization makes it easier to run the same artifact locally, in CI, and in production.
- 12-factor practices (env-config, stateless processes, logs to stdout/stderr) simplify scaling and deployment to Kubernetes or managed container platforms later.
- Postgres remains a single, managed instance for MVP, avoiding early complexity around replication and sharding.

**Alternatives considered**:
- **Non-containerized deployment on a single VM**: Quicker to set up initially but harder to integrate with modern CI/CD and cloud-native tooling.
- **Fully managed PaaS (e.g., Heroku-style)**: Could be used later, but the plan aims to remain vendor-neutral.

---

## CI/CD with GitHub Actions

**Decision**: Use GitHub Actions workflows for linting, testing, building Docker images, and preparing for deployment.

**Rationale**:
- GitHub Actions integrates tightly with GitHub repositories and supports multi-stage workflows and container registries.
- A standard pipeline (lint → test → build image → deploy to test/staging) fits this project’s needs.
- Automating tests and image builds enforces the constitution’s engineering quality and testing discipline.

**Alternatives considered**:
- **GitLab CI**: Also a strong option but this project will be hosted on GitHub, so aligning source control and CI/CD on a single platform is preferred.
- **Manual deployments**: Too fragile and inconsistent with a cloud-native-first approach.

---

## Observability and Logging

**Decision**: Implement basic structured logging and minimal application metrics, avoiding sensitive content in logs.

**Rationale**:
- Aligns with the constitution’s guidance on security, privacy, and observability.
- Enables debugging of clipping flows (clip created, search performed, API failures) without logging actual clipped text.

**Alternatives considered**:
- **Rich distributed tracing from day one**: Overkill for an MVP and can be added later if/when distributed components are introduced.
