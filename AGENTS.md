# AGENTS.md — MultipliQuest

Instructions for Codex and other coding agents working in this repository. Read `README.md` before changing code. The README is the product specification; this file defines implementation and collaboration rules. If a requirement is ambiguous or conflicts with another requirement, **ask the maintainer before making a product decision**. Do not silently change progression thresholds or pedagogical rules.

## 1. Mission and scope

Build a small, secure, responsive browser game for a child to practise multiplication tables **2 through 12**. Prioritize correctness, clarity, accessibility and an encouraging experience over visual complexity. The MVP is single-player per child profile, without public leaderboards, chat, ads, purchases or generative AI.

Deliver features in small, independently testable increments. Do not implement speculative features from the README's future-ideas section unless explicitly requested.

## 2. Source of truth and unresolved decisions

- `README.md`: product rules, user journeys, acceptance criteria.
- `AGENTS.md`: engineering conventions and agent workflow.
- Tests: executable documentation of agreed behavior; if tests contradict the README, flag the discrepancy instead of changing product rules silently.
- Before a significant architectural change or a new external service, present options and obtain approval.
- Do not assume an existing project structure, package, dependency, environment variable or deployment provider: inspect the repository first.

## 3. Non-negotiable game rules

### Levels and available tables

| Level | Available tables | Newly unlocked table |
| --- | --- | --- |
| 1 | 2, 3, 4 | Initial tables |
| 2 | 2–5 | 5 |
| 3 | 2–6 | 6 |
| 4 | 2–7 | 7 |
| 5 | 2–8 | 8 |
| 6 | 2–9 | 9 |
| 7 | 2–10 | 10 |
| 8 | 2–11 | 11 |
| 9 | 2–12 | 12 |

Multipliers range from **1 to 12**. Each session contains **exactly 20 questions**, with no time limit and a numeric free-text answer. At level 1, distribute questions across tables 2, 3 and 4. From level 2 onward, **at least 10 of 20 questions** must concern the newly unlocked table; draw the others from earlier tables, ensuring those tables continue to appear across sessions. Avoid immediate repetition where feasible. `3 × 4` and `4 × 3` may be distinct questions.

### Unlocking and mastery

- **Level 1 → 2:** at least **19/20 correct in one completed level-1 session**.
- **Levels 2 → 9:** BOTH of the following must be true at the current level:
  1. At least **19/20 correct in one completed session** at that level. Once achieved, this condition remains satisfied for that level.
  2. At least **19/20 correct in the latest 20 attempts on the newly unlocked table**, drawn from **completed sessions at the current level**. Fewer than 20 eligible attempts means mastery is not yet evaluable. This is a rolling window, not a lifetime average.
- The two conditions may be satisfied in different sessions. Re-evaluate progression after a session is completed and its attempts are persisted.
- Incomplete/abandoned sessions contribute **neither** to the global condition **nor** to the mastery window.
- On unlocking the next level, its new table begins a fresh mastery window; retain historical attempts.
- Unlocks, earned XP and trophies are permanent; later errors do not revoke them.
- At **level 9**, meeting both conditions awards the final trophy instead of unlocking level 10.

Important edge case: a session that first satisfies global success can also supply eligible attempts for mastery once completed. Do not double-count attempts when a completion request is retried.

### XP and trophies

- **10 XP** per correct answer; **20 bonus XP** for a completed session scoring at least 19/20. No XP deduction for errors.
- XP does **not** unlock tables.
- Trophies (once per profile): first completed session, 20/20 session, unlock table 5, five completed sessions, and completion of level 9's two mastery conditions.
- Feedback on incorrect answers must show the correct result and remain supportive; do not penalize response time.

## 4. Intended technical stack

Use the README's proposed stack unless the maintainer decides otherwise:

- Backend: **Python, Django, Django REST Framework**; manage Python and dependencies with **`uv`**.
- Frontend: **React, TypeScript, Vite**.
- Development database: **SQLite**; production: **PostgreSQL if appropriate for the chosen hosting**.
- Quality: **Ruff, mypy, pytest** and API tests; **Playwright** for a few end-to-end user journeys.
- Version control / CI: **GitHub and GitHub Actions**.

Keep a straightforward monolith backend and one frontend. No microservices, message queues, Celery, Redis, analytics platform or external identity provider without a demonstrated need and approval. Do not introduce Docker as a prerequisite unless agreed.

## 5. Architecture and code conventions

- Write **English identifiers** (modules, classes, variables, functions and API fields); user-facing text should be in **French**.
- Use descriptive names, type annotations for new Python code and strict TypeScript types. Avoid `Any`/`any` without justification.
- Keep views/viewsets and serializers thin. Put question generation, session completion, scoring, rolling-window evaluation, unlocking and trophy attribution in **small, testable domain services**.
- Persist facts (sessions, attempts, awards); derive available tables from the current level rather than duplicating them without need.
- Prefer explicit service calls to Django signals for core gameplay. Avoid clever abstractions and premature generalization.
- Use database constraints for invariants, including uniqueness of `(player, trophy)` and of an attempt's position within a session. Consider unique client-safe submission identifiers if needed for retries.
- Complete a session and award XP/trophies/unlocks **atomically**; make the operation **idempotent**. Handle concurrent duplicate completion requests safely.
- The server owns question selection and answer checking. Never trust a client-supplied score, XP amount, unlocked level, correct answer or trophy. Do not expose the correct answer before submission through the normal gameplay API.
- Decide and document how sessions resume after reload, how abandoned sessions are represented, and how generated questions are persisted before implementing those features.
- Keep configuration in environment variables; include `.env.example` with **placeholders only**. Never commit `.env`, credentials, tokens or real child data.

## 6. Test-first workflow

For every business-rule change:

1. Read the relevant README section and inspect existing code/tests.
2. Summarize the intended behavior and list edge cases.
3. Write failing tests for the agreed behavior (TDD where practical).
4. Implement the smallest change that makes them pass.
5. Refactor without changing behavior; run the relevant checks.
6. Report changed files, test commands/results and any unresolved risks.

Mandatory domain tests include:

- Starting tables 2–4; correct level-to-table mapping through level 9; no table 13/level 10.
- Exactly 20 questions; valid operands 1–12; at least 10 questions on the newest table from level 2; old tables remain eligible.
- Level 1: 18/20 does not unlock, 19/20 and 20/20 do.
- Levels 2–9: global success alone does not unlock; mastery alone does not unlock; both together do, even across separate completed sessions.
- Mastery: 19/20 succeeds, 18/20 fails, fewer than 20 eligible attempts fails; rolling window drops the oldest attempt; only completed sessions at the **current level** count.
- Incomplete sessions do not count for either condition. Retrying session completion never duplicates attempts, XP, trophies or unlocks.
- The final level awards the final trophy rather than creating another level.
- Cross-user authorization: one account cannot read or mutate another child's progress.
- API validation: malformed answers, duplicate submissions and unexpected fields cannot alter server-calculated scores.

Use deterministic random seeds or injectable randomness in generation tests; do not make tests probabilistic. Add integration tests for transactions and a small Playwright smoke path for a complete session. Mock only external boundaries, not core domain behavior.

Suggested checks **once the corresponding tools/configurations exist** (inspect actual paths and commands first):

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
# In the frontend directory, once scripts are configured:
npm run lint
npm run build
npm run test
```

Do not claim a check passed unless you ran it. If dependencies or services are unavailable, state exactly what could not be verified. Do not weaken tests or disable lint rules merely to obtain a green result.

## 7. Child privacy, authentication and security

Treat child privacy as a design constraint, not a post-launch task:

- A **parent account** owns one or more private child profiles; child profiles use a **pseudonym**, not their own email. Ask before implementing any independent child login.
- Enforce object-level authorization on every profile, session, attempt and trophy endpoint. Do not rely on hidden frontend controls for permissions.
- Use Django's established authentication/session mechanisms, HTTPS in production, secure/HttpOnly/SameSite cookies as appropriate, CSRF protection, server-side validation and rate limiting for login endpoints.
- Set `DEBUG=False` in production; configure allowed hosts, CORS narrowly if needed, security headers, secret management and dependency checks.
- Collect the minimum data necessary. No public profiles, chat, advertising, third-party tracking or sensitive personal data in logs.
- Avoid leaking account existence or secrets through errors. Keep logs useful but privacy-preserving.
- Add tests for unauthorized and cross-account access. Run Django's deployment checks before launch.
- Do not perform production database migrations, delete data, expose services or deploy without explicit maintainer approval.

## 8. Frontend and accessibility

- Mobile-first responsive UI, also usable on desktop and tablet.
- Large tap targets, clear focus states, keyboard navigation and accessible form labels; never rely solely on color to indicate correctness.
- Explain incorrect answers without shame. No countdown timer, public comparison or loss of earned rewards.
- Display **two distinct progress indicators** at levels 2–9: best completed-session result at the current level, and correct answers among the last 20 eligible attempts on the newest table. Before 20 attempts, show progress toward the required sample rather than a misleading mastery percentage.
- Show the current level, available tables, session results, XP and earned trophies; keep animations short and non-blocking.
- Do not invent new reward mechanics or modify thresholds without approval.

## 9. Git, review and agent boundaries

- Work on a feature branch when the repository workflow supports it. Make focused commits with descriptive messages; do not rewrite unrelated history.
- Before edits, inspect `git status` and preserve pre-existing user changes. Never discard uncommitted work or run destructive commands without approval.
- Prefer small diffs. Do not reformat unrelated files, add dependencies or alter deployment configuration outside the requested scope.
- Do not autonomously merge, publish, deploy, change repository permissions or access production.
- When delegating to subagents, give each a bounded task and file scope; avoid concurrent edits to the same files. Integrate and review their output before considering work complete.
- Flag security findings and ambiguous requirements; do not silently substitute a guess.

## 10. Suggested implementation order

1. Initialize backend/frontend, development commands, CI skeleton and test tooling.
2. Implement question generation and deterministic tests.
3. Implement session lifecycle, persisted questions/attempts and server-side scoring.
4. Implement the two independent 95% conditions and rolling mastery window, with boundary tests.
5. Implement durable player progression, idempotent XP and trophies.
6. Build playable French-language screens and the two progress indicators.
7. Add parent authentication, child-profile authorization and security tests **before any public deployment**; design ownership into the data model from the start.
8. Add end-to-end tests, production settings, backups and an approved deployment process.

At the end of each task, provide: **summary**, **files changed**, **tests run and results**, **known limitations**, and **next suggested small task**. If a choice affects pedagogy, privacy, costs or hosting, ask the maintainer instead of deciding unilaterally.
