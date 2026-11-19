# Verification report (actual executed checks)

## Authoring environment

Python 3.13, SQLite, Jinja2 and pytest installed. **Flask and Werkzeug were not installed**, and an attempt to install them using pip failed because package-index DNS/network access was unavailable. Headless browser navigation to file:// and localhost URLs was blocked by administrator policy. A **standalone, fully inlined design preview** could still be rendered through Chromium page content injection, allowing visual and interactive frontend checks. No claim of a successful Flask server run or web end-to-end test is made.

## Actually executed

Command: `python scripts/offline_verify.py`

- PASS — all authored Python files compile as source.
- PASS — seven principal SQLite tables exist with foreign keys enabled.
- PASS — a pending voter cannot vote.
- PASS — a candidate from another election and a closed/future election are rejected.
- PASS — deliberate failure between participation and ballot inserts rolls back both.
- PASS — two concurrent writes using **two separate SQLite connections** result in exactly one accepted ballot.
- PASS — results remain private before publication; published results include a zero-vote candidate.

Command: Jinja `Environment(...).get_template(...)` compile loop, with custom date filters registered.

- PASS — all 18 Jinja templates parse successfully after a syntax issue in the student verification template was corrected.

Command: Chromium/Playwright `page.set_content` using the standalone design-only preview (fictional sample data).

- PASS — administrator and student desktop dashboards rendered at 1440 px wide without horizontal overflow.
- PASS — mobile layout rendered at 390 px wide with no horizontal page overflow.
- PASS — mobile navigation opened and closed using the menu/scrim.
- PASS — candidate selection → review-vote confirmation dialog → cancel works in the standalone voting-screen preview.
- PASS — desktop theme toggle switched from light to dark and back.
- NOTE — these checks do not exercise Flask routes, session handling or database connectivity.

## Not verified end-to-end here

- `python -m pytest tests -q` was **attempted** but stopped during collection (exit code 4): `ModuleNotFoundError: No module named werkzeug`. Therefore no Flask route tests ran.
- Real Flask server boot, real form submission in browser, login throttling, live Flask browser review (static standalone desktop/mobile screenshot checks were completed).
- Full automated accessibility audit.

**Recommended next step in Windows VS Code:** install `requirements.txt`; run the pytest suite, start the app, and check desktop/tablet/mobile views before demonstrating or using any real user data. Report any failures instead of treating this report as deployment certification.

Additional check: `node --check campusvote/static/js/main.js` completed successfully.
