# Shortly — Learning Log

**Goal:** Go from tutorial-level sync FastAPI to hireable backend engineer.
**Project:** URL shortener that grows into a production-grade service.
**Repo:** github.com/<you>/shortly

## Working agreement (coach ↔ student)

- Coach: hard tone, strict review, no advancing without passing.
- Student: writes first drafts of everything new. Cline (AI agent) is a teammate,
  not a crutch.
- **Green/Yellow/Red rule:** Green = boilerplate, Cline writes. Yellow = Cline
  refines my draft. Red = I write, Cline only reviews after.
- Every lesson ends with: passing acceptance tests, `NOTES.md` update, git commit.
- "Explain it back" before moving on. If I can't explain it, I don't know it.
- Time budget: 25+ hrs/week.

## Repo layout
shortly/
├── app/
│ ├── init.py
│ └── main.py
├── tests/ (coming in Lesson 2)
├── pyproject.toml
├── NOTES.md
└── uv.lock

## Tooling

- Python 3.12 (pinned in `.python-version`)
- uv for deps + venv
- FastAPI + uvicorn
- Running in Fedora toolbx container (`⬢ [dilaferaw@toolbx]`)

---

## Lesson 1 — In-memory URL shortener ✅

**Date:** 2026-10-06
**Status:** PASS (9/9 curl tests)

### What was built

Two endpoints in `app/main.py`, no DB, in-memory dicts:

- `POST /shorten` — accepts `{url, custom_code?}`, returns
  `{short_url, code, original_url, created}`
- `GET /{code}` — 302 redirect to original URL, or 404

### Design decisions made (and why)

1. **302 not 301** — 301 gets cached aggressively by browsers. If we ever want to
   change where a code points, users would be stuck going to the old destination.
   302 = temporary, no poisoning user caches.
2. **Idempotent shorten** — same URL submitted twice returns the same code with
   `created: false`. Matches TinyURL. Simpler contract than per-click codes.
   Implemented with a second dict (`url_to_code`) alongside `code_to_url`.
3. **Lowercase-only codes** — enforced via `StringConstraints` pattern
   `^[a-z0-9]+$`. Reduces confusion when users type codes from memory, and avoids
   case-insensitivity collision bugs.
4. **Collision loop** — with 36^6 ≈ 2.18B possible codes, birthday paradox means
   ~50% collision risk around 60k links. Without the retry loop, we'd silently
   overwrite existing mappings. Loop on collision.
5. **Reserved codes** — `docs`, `redoc`, `shorten`, `admin`, `openapi.json`,
   `health` are blocked as custom codes so they can't shadow system routes.
6. **No trailing slash** — `/abc123` works, `/abc123/` returns 404. Short URLs
   should be exact. Removed default FastAPI trailing-slash redirect behavior.

### Bugs hit and fixed (worth remembering)

- **Half-refactor bug:** introduced local `code` variable but forgot to update
  `short_url` f-string. Response returned `/None` for the URL while `code` was
  the generated value. **Lesson:** when refactoring, grep for the old name
  everywhere. Half-refactors are worse than none.
- **307 vs 302:** initially used 307. Wrong — 307 preserves the HTTP method, so
  a POST to a short URL would POST to the destination. Nonsense for a shortener.
- **Trailing slash on route:** `@app.get("/{code}/")` caused FastAPI to
  auto-redirect `/dila` → `/dila/` with a 307, bypassing the handler entirely.
  Removed the slash.

### Concepts learned

- `HttpUrl` in Pydantic v2 normalizes URLs (`https://example.com` →
  `https://example.com/`). Handles scheme validation for free; rejects
  `javascript:`, `data:`, `file:` etc. with a 422.
- FastAPI's `redirect_slashes` default behavior. Know it exists.
- `secrets.choice` > `random.choice` for anything user-facing (cryptographically
  secure).
- 422 (FastAPI validation) vs 400 (bad request we raise ourselves) — know the
  difference.
- Don't mutate Pydantic input models. Use local variables.

### Current limitations (deliberate — fixed in later lessons)

- Data dies on restart (no persistence) → **Lesson 3: Postgres**
- Not async → **Lesson 5: async SQLAlchemy**
- Hardcoded `localhost:8000` in responses → **Lesson 7: deploy**
- No tests → **Lesson 2 (next)**
- No click analytics, no auth, no rate limiting → later lessons

### Next up

**Lesson 2 — Tests.** pytest, TestClient, fixtures, test isolation.
Specifically: the module-level `tmp_db` dict will cause cross-test pollution
without a reset fixture.

---

## Lesson 2 — Tests ⏳ (in progress)

Started 2026-10-06. Will update when passed.

---

## Lesson 2 — Tests ✅

**Date:** 2026-10-07
**Status:** PASS (11/11 tests, 98% coverage on app/main.py)

### What was built

- `tests/conftest.py` — two fixtures: `client` (TestClient wrapper) and
  `reset_db` (autouse, clears tmp_db before every test)
- `tests/test_shortener.py` — 11 tests covering every behavior from Lesson 1's
  curl suite, plus two extra validation cases and a randomness smoke test
- `pyproject.toml` — added `[tool.pytest.ini_options] testpaths = ["tests"]`
- `.gitignore` — coverage artifacts, caches, .venv

### Concepts learned

- **pytest basics:** test functions named `test_*`, `assert` statements,
  discovery via `testpaths`, `-v` for verbose.
- **Fixtures:** `@pytest.fixture` decorator. Request them as function
  parameters. `autouse=True` means "run for every test without opt-in."
- **`conftest.py`:** special file pytest reads automatically. Fixtures defined
  here are available to all tests in the folder.
- **TestClient:** in-process HTTP client via `fastapi.testclient`. No server
  needed. `follow_redirects=False` for testing 3xx responses.
- **Test isolation:** each test must start from identical state regardless of
  order. The module-level `tmp_db` dict breaks this without the reset fixture.
- **Behavior vs implementation:** test `created is True`, not `code == "abc123"`.
  The first verifies product behavior; the second couples the test to the RNG.
- **`is` vs `==` for booleans:** `is True/False` is identity, `== True/False` is
  equality. `1 == True` in Python, so `==` is weaker. Use `is`.

### Three questions (my answers, in my own words)

1. **Why `autouse=True` on `reset_db`:**
   <you write this — what breaks without it, why not opt-in>

2. **Why `is True` beats `== "abc123"`:**
   <you write this — behavior vs implementation, what breaks when RNG changes>

3. **What "test isolation" means:**
   <you write this — the specific failure mode, order-dependence>

### Bugs hit and fixed

- Committed `tests/.coverage` (binary artifact). Fixed with
  `git rm --cached tests/.coverage` + `.gitignore`. Learned: never commit
  generated files.
- `== True` / `== False` in assertions. Switched to `is`.
- `test_shorten_invalid_custom_code` was testing two things (uppercase
  rejection AND length rejection). Split into two tests. Rule: one test, one
  behavior. If the test name needs "and," split it.
- Line 76 (collision retry inside `while`) is uncovered. Effectively untestable
  without mocking `secrets.choice`. Noted, deferred to a later lesson on mocks.

### Current limitations

- State is still in-memory. Tests are coupled to the module-level `tmp_db`.
  When we move to Postgres in Lesson 3, `reset_db` gets replaced with proper
  transaction rollback per test.
- Starlette deprecation warning about `httpx` vs `httpx2` — ignored for now,
  the async client in Lesson 5 sidesteps it.

### Next up

**Lesson 3 — Postgres + Alembic.** Replace `tmp_db` with real persistence.
Async SQLAlchemy 2.0. Migration from in-memory to DB-backed without breaking
the tests.