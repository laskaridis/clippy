# webclippings Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-15

## Active Technologies
- Python 3.11+ (targeting 3.12 where available), JavaScript for the Chrome extension + Django 5.x, Django REST Framework, Django auth/session middleware, Jest (or equivalent) for extension tests (001-web-clipping-app)
- PostgreSQL as primary datastore; Django ORM models for `User`, `Clip`, `Label`, and `ClipLabel` (001-web-clipping-app)

- Python 3.11+ (target 3.12 where available) + Django 5.2, Django REST Framework (for JSON APIs), psycopg2-binary (PostgreSQL driver) (001-web-clipping-app)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+ (target 3.12 where available): Follow standard conventions

## Recent Changes
- 001-web-clipping-app: Added Python 3.11+ (targeting 3.12 where available), JavaScript for the Chrome extension + Django 5.x, Django REST Framework, Django auth/session middleware, Jest (or equivalent) for extension tests

- 001-web-clipping-app: Added Python 3.11+ (target 3.12 where available) + Django 5.2, Django REST Framework (for JSON APIs), psycopg2-binary (PostgreSQL driver)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
