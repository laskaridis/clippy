# Manual Smoke Checklist

- Executed: 2026-03-27 12:40:16 EET
- Method: Playwright headless smoke pass (desktop + mobile viewports) against local worktree runtime
- Base URL: http://clippy-d30c7e.localhost:8294

| Viewport | Route | Check | Result | Evidence |
|---|---|---|---|---|
| desktop | home | load | PASS | http://clippy-d30c7e.localhost:8294/ |
| desktop | accounts-login | load | PASS | http://clippy-d30c7e.localhost:8294/accounts/login/ |
| desktop | accounts-register | load | PASS | http://clippy-d30c7e.localhost:8294/accounts/register/ |
| desktop | accounts-password-reset | load | PASS | http://clippy-d30c7e.localhost:8294/accounts/password-reset/ |
| desktop | accounts-password-reset-done | load | PASS | http://clippy-d30c7e.localhost:8294/accounts/password-reset/done/ |
| desktop | accounts-password-reset-complete | load | PASS | http://clippy-d30c7e.localhost:8294/accounts/reset/done/ |
| desktop | accounts-password-reset-confirm | load | PASS | http://clippy-d30c7e.localhost:8294/accounts/reset/Mw/d63hcn-3b18911647757ceb492f2fff560976c1/ |
| desktop | accounts-activate | load | PASS | http://clippy-d30c7e.localhost:8294/accounts/activate/Mw/d63hcn-3b18911647757ceb492f2fff560976c1/ |
| desktop | accounts-login | primary-action-login | PASS | http://clippy-d30c7e.localhost:8294/clips/ |
| desktop | clips-list | load | PASS | http://clippy-d30c7e.localhost:8294/clips/ |
| desktop | clips-list | primary-action-open-detail | PASS | http://clippy-d30c7e.localhost:8294/clips/5edacbae-327e-49b0-8d1b-929bda6293ed/ |
| desktop | clips-detail | load | PASS | http://clippy-d30c7e.localhost:8294/clips/5edacbae-327e-49b0-8d1b-929bda6293ed/ |
| desktop | clips-detail | primary-action-back-to-list | PASS | http://clippy-d30c7e.localhost:8294/clips/ |
| desktop | clips-labels | load | PASS | http://clippy-d30c7e.localhost:8294/clips/labels/ |
| desktop | clips-labels | primary-action-navigate-list | PASS | http://clippy-d30c7e.localhost:8294/clips/ |
| desktop | console | error | PASS | No console errors captured (excluding favicon-related 404 noise) |
| desktop | network | http>=400 | PASS | No HTTP >=400 responses (excluding favicon, activation token reuse) |
| mobile | home | load | PASS | http://clippy-d30c7e.localhost:8294/ |
| mobile | accounts-login | load | PASS | http://clippy-d30c7e.localhost:8294/accounts/login/ |
| mobile | accounts-register | load | PASS | http://clippy-d30c7e.localhost:8294/accounts/register/ |
| mobile | accounts-password-reset | load | PASS | http://clippy-d30c7e.localhost:8294/accounts/password-reset/ |
| mobile | accounts-password-reset-done | load | PASS | http://clippy-d30c7e.localhost:8294/accounts/password-reset/done/ |
| mobile | accounts-password-reset-complete | load | PASS | http://clippy-d30c7e.localhost:8294/accounts/reset/done/ |
| mobile | accounts-password-reset-confirm | load | PASS | http://clippy-d30c7e.localhost:8294/accounts/reset/Mw/d63hcn-3b18911647757ceb492f2fff560976c1/ |
| mobile | accounts-activate | load | PASS | http://clippy-d30c7e.localhost:8294/accounts/activate/Mw/d63hcn-3b18911647757ceb492f2fff560976c1/ |
| mobile | accounts-login | primary-action-login | PASS | http://clippy-d30c7e.localhost:8294/clips/ |
| mobile | clips-list | load | PASS | http://clippy-d30c7e.localhost:8294/clips/ |
| mobile | clips-list | primary-action-open-detail | PASS | http://clippy-d30c7e.localhost:8294/clips/5edacbae-327e-49b0-8d1b-929bda6293ed/ |
| mobile | clips-detail | load | PASS | http://clippy-d30c7e.localhost:8294/clips/5edacbae-327e-49b0-8d1b-929bda6293ed/ |
| mobile | clips-detail | primary-action-back-to-list | PASS | http://clippy-d30c7e.localhost:8294/clips/ |
| mobile | clips-labels | load | PASS | http://clippy-d30c7e.localhost:8294/clips/labels/ |
| mobile | clips-labels | primary-action-navigate-list | PASS | http://clippy-d30c7e.localhost:8294/clips/ |
| mobile | console | error | PASS | No console errors captured |
| mobile | network | http>=400 | PASS | No HTTP >=400 responses (excluding favicon, activation token reuse) |
