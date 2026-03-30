# miminions_website Fixes and Improvements Plan

Date: 2026-03-30

This plan is organized by implementation phase so critical risk is reduced first, then reliability and product quality improve in controlled steps.

## Phase 0 - Immediate Safety and Hygiene (same day)

1. Remove local user data from the repository and ignore it.
- Why: `users_local_db.json` currently contains real email addresses and password hashes.
- Actions:
  - Remove tracked sensitive local DB file from git history in a follow-up security cleanup.
  - Add `*_local_db.json` and `users_local_db.json` to `.gitignore`.
  - Keep only a sanitized sample if needed (for example `users_local_db.example.json`).
- Files:
  - `users_local_db.json`
  - `.gitignore`

2. Stop running local mode as Flask testing mode.
- Why: `get_config()` returns `TestingConfig` for non-production, which can alter runtime behavior and mask real issues.
- Actions:
  - Return `DevelopmentConfig` for local development.
  - Reserve `TestingConfig` only for explicit test execution.
- Files:
  - `apps/config.py`

3. Lock down environment safety checks.
- Why: Missing secrets can result in insecure runtime or startup surprises.
- Actions:
  - Enforce `SECRET_KEY` for all non-test environments.
  - Ensure production fails fast if mail/JWT configs are missing.
  - Replace `print(...)` warnings with structured logging.
- Files:
  - `apps/config.py`

## Phase 1 - Security Hardening (1-2 days)

1. Make logout CSRF-safe.
- Why: Logout is currently a GET route, which is vulnerable to CSRF-triggered sign-out.
- Actions:
  - Change logout endpoint to POST only.
  - Update navbar/logout UI to use a small POST form with CSRF token.
- Files:
  - `apps/auth/routes.py`
  - `templates/base.html`

2. Tighten CSP and external asset policy.
- Why: `landing.html` uses assets from cdnjs, but CSP only allows jsdelivr/google fonts, causing policy drift and possible blocked assets.
- Actions:
  - Either self-host Font Awesome and other external assets, or explicitly allow required origins.
  - Add `object-src 'none'` and `base-uri 'self'`.
  - Consider request nonce strategy for inline script/style evolution.
- Files:
  - `apps/__init__.py`
  - `templates/landing.html`
  - `templates/base.html`

3. Improve proxy trust boundaries.
- Why: ProxyFix is applied unconditionally; direct access to app instances can make forwarded headers untrusted.
- Actions:
  - Apply ProxyFix only in production or behind verified reverse proxy.
  - Include explicit `x_for` handling if real client IP is required for rate limiting.
- Files:
  - `apps/__init__.py`
  - `apps/extensions.py`

4. Harden contact/email injection surfaces.
- Why: Contact form data is interpolated into HTML emails without escaping/sanitization.
- Actions:
  - Escape user-controlled fields before composing HTML email.
  - Add max length validation for name/message/phone.
- Files:
  - `apps/main/routes.py`
  - `apps/email_service.py`
  - `apps/utils.py`

## Phase 2 - Auth and Abuse Prevention (2-3 days)

1. Improve password policy and auth ergonomics.
- Why: Current password validation only enforces length >= 8.
- Actions:
  - Add stronger baseline policy (length, character variety, deny common weak passwords).
  - Return user-friendly validation messages.
- Files:
  - `apps/utils.py`
  - `apps/auth/routes.py`
  - `templates/signup.html`
  - `templates/profile.html`

2. Add targeted anti-abuse controls.
- Why: Login/signup limits exist, but no progressive lockout, no contact form limit, and limiter storage is in-memory only.
- Actions:
  - Add per-IP + per-account failed-login throttling.
  - Rate limit `/contact`.
  - Move Flask-Limiter storage to Redis in production.
- Files:
  - `apps/extensions.py`
  - `apps/auth/routes.py`
  - `apps/main/routes.py`

3. Reduce sensitive authentication logging.
- Why: Current logs include full user email for auth attempts.
- Actions:
  - Redact or hash identifying details in auth logs.
  - Keep full details only at debug level behind secure controls.
- Files:
  - `apps/auth/routes.py`

## Phase 3 - Data Correctness and Concurrency (2-4 days)

1. Replace read-modify-write patterns with conditional DynamoDB writes.
- Why: Current `add_user` and `update_user` can race under concurrent requests.
- Actions:
  - Use `ConditionExpression` for create (`attribute_not_exists(email)`).
  - Use `update_item` with explicit attribute updates instead of full `put_item` overwrite.
  - Handle conditional write failures cleanly.
- Files:
  - `apps/store.py`

2. Improve data model consistency.
- Why: Local mock assumes flexible keys and can diverge from production table behavior.
- Actions:
  - Standardize partition key assumptions and validation.
  - Keep mock behavior close to DynamoDB semantics.
- Files:
  - `apps/database.py`
  - `apps/store.py`

3. Prevent error detail leakage in health endpoint.
- Why: `/health` currently returns raw exception strings.
- Actions:
  - Return generic error to clients.
  - Keep detailed exception data only in server logs.
- Files:
  - `apps/main/routes.py`

## Phase 4 - UX and Frontend Reliability (1-2 days)

1. Fix external link safety and consistency.
- Why: External links with `target="_blank"` should include `rel="noopener noreferrer"`.
- Actions:
  - Update all external anchor tags.
- Files:
  - `templates/base.html`
  - `templates/landing.html`

2. Improve form resilience and accessibility.
- Why: Validation errors currently clear user-entered form fields in several templates.
- Actions:
  - Re-populate non-sensitive fields after validation failures.
  - Ensure explicit `aria-describedby` for helper text and errors.
  - Add client-side max lengths aligned with backend validation.
- Files:
  - `apps/auth/routes.py`
  - `apps/main/routes.py`
  - `templates/signup.html`
  - `templates/contact.html`
  - `templates/profile.html`

3. Make password toggle script defensive.
- Why: Missing DOM elements can produce JS errors.
- Actions:
  - Guard for null input/icon before class/type mutations.
- Files:
  - `static/js/password-toggle.js`

## Phase 5 - Quality, Testing, and Operations (3-5 days)

1. Add baseline automated tests.
- Why: No test suite exists for auth, validation, and route behavior.
- Actions:
  - Add unit tests for validation helpers.
  - Add integration tests for signup/login/verify/profile/contact.
  - Add tests for CSRF-protected POST endpoints.
- Files:
  - New: `tests/`
  - `apps/utils.py`
  - `apps/auth/routes.py`
  - `apps/main/routes.py`

2. Add dev tooling and CI checks.
- Why: No automated gate for style, security, or regressions.
- Actions:
  - Add formatter/linter/type checks (black, ruff, mypy optional).
  - Add dependency vulnerability scanning.
  - Add CI workflow for tests + lint on pull requests.
- Files:
  - New: `.github/workflows/ci.yml`
  - New: `pyproject.toml` (or equivalent tool config)

3. Improve observability and runbooks.
- Why: Logs are present but not structured for reliable operations.
- Actions:
  - Add request ID correlation and structured logging format.
  - Document incident playbooks for auth/email/database failures.
  - Add deployment checklist (env vars, limiter backend, health checks).
- Files:
  - `apps/__init__.py`
  - `README.md`

## Phase 6 - Documentation Cleanup (0.5-1 day)

1. Clean README and environment docs.
- Why: Setup instructions are good but can be clearer on local vs test vs production behavior.
- Actions:
  - Clarify config modes and command flags.
  - Fix section numbering and add troubleshooting notes.
  - Document expected local email behavior when `RESEND_API_KEY` is absent.
- Files:
  - `README.md`
  - `example.env`

2. Reduce repo noise and duplication.
- Why: `.gitignore` has duplicated sections and mixed language ecosystem entries.
- Actions:
  - De-duplicate and trim irrelevant rules.
  - Keep Python/Flask-focused ignore patterns.
- Files:
  - `.gitignore`

## Suggested Execution Order

1. Phase 0
2. Phase 1
3. Phase 2 and Phase 3 in parallel (separate branches)
4. Phase 4
5. Phase 5
6. Phase 6

## Definition of Done per Phase

1. Code changes merged with tests (or at least manual verification checklist).
2. No new app errors in startup and core auth/contact flows.
3. README updated when behavior/config changes.
4. Security-sensitive changes validated in production-like environment.