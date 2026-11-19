# CampusVote — Online Voting System

A local-first Python, Flask, SQLite web application for an academic college election demonstration. The UI is custom-built to match the provided **white + charcoal + emerald + mint + peach analytics dashboard** reference (not a sales dashboard). It uses CSS-only graphics, a bundled SVG icon sprite, accessible forms, responsive cards and a dark-mode switch.

## What is included

- Student registration (new registrations are `pending`), sign-in, profile and password change.
- Administrator-only student approval/rejection and searchable directory.
- Election drafts, schedule editing, eligible-voter selection and candidate add/edit/remove.
- Deterministic election lifecycle: `draft → scheduled → open → closed → published` (time-derived open/closed stages).
- Individual student dashboards with assigned elections, candidate cards and a ballot confirmation dialog.
- Server-checked one-vote-per-student-per-election transactions, duplicate prevention and anonymous-style receipt.
- Aggregate turnout, published results, tie handling, zero-vote candidates and CSV result export.
- Audit events that do not record candidate choices.
- Fully local CSS/JavaScript/SVG (no online assets, npm, third-party API or external CDN).
- Optional fictional demo seed, test suite and documentation.

**Prototype note:** The system is suitable for coursework and a local demonstration. It is not a certified, independently verifiable public election system, and SQLite administrators may be able to correlate ballots with participation through timing or file access. See `docs/SECURITY_LIMITATIONS.md`.

## Start in VS Code on Windows 10/11

1. Extract the project ZIP. Open the `CampusVote` folder in VS Code (`File → Open Folder`).
2. Open **Terminal → New Terminal** (PowerShell).
3. Run:

```powershell
py -3 --version
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, use `cmd` and `.venv\Scripts\activate.bat` instead. Alternatively, use `.\.venv\Scripts\python.exe` to run commands without activating.

4. Create your administrator (choose your own ID and strong password when prompted):

```powershell
python -m flask --app run.py create-admin
```

5. Optional: populate **fictional** demo students/candidates/elections and copy the random demo voter password shown in the terminal:

```powershell
python scripts/seed_demo.py
```

6. Start the application:

```powershell
python run.py
```

7. Open **http://127.0.0.1:5000** in your browser. Sign in with the administrator ID/password you created. For demo voting, log in as `STU001` with the random password printed by the seed script.

Stop the server with **Ctrl+C**. The SQLite database is created automatically under `instance/campusvote.sqlite3`; the local Flask session secret is generated under `instance/.secret_key`. Both are excluded from version control and the distribution ZIP.

> Run only on `127.0.0.1` for the college demo. The built-in Flask server is not a production application server.

## How to use the UI

**Administrator:** Dashboard → Student Verification → Elections → Create election → Add 2+ candidates → Select eligible approved students → Finalize & schedule → Monitor turnout → Close voting → Publish results → Reports.

**Student:** Register → Wait for admin approval → Log in → My Elections → Select an open election → Choose one candidate → Review vote → Confirm → Save your neutral receipt → See results after publication.

**Important:** The vote is validated by Flask and SQLite, not merely by the browser confirmation dialog. Submission is atomic and irreversible after acceptance.

## Running tests

After installing free dependencies:

```powershell
python -m pytest tests -q
python scripts/offline_verify.py
```

`offline_verify.py` exercises actual SQLite schema and voting/result service code without needing Flask installed. Full web workflow tests require Flask. The included `docs/TEST_REPORT.md` accurately separates checks executed during artifact creation from tests not executed in that environment.

## Database and reset

To back up the database, stop Flask and copy `instance/campusvote.sqlite3` somewhere safe. For a **fresh disposable demo** only, stop Flask, move the database file out of the `instance` folder, restart and create a new admin, then rerun `seed_demo.py`. **Never delete a database containing work you want to keep.** The seed script refuses to overwrite existing seeded student IDs.

## Project tree

```text
CampusVote/
├── run.py, requirements.txt, README.md, QUICK_START_WINDOWS.md
├── campusvote/
│   ├── __init__.py, db.py
│   ├── auth/routes.py
│   ├── admin/routes.py
│   ├── voting/routes.py
│   ├── services/vote_service.py, result_service.py
│   ├── templates/ (18 Flask/Jinja pages)
│   └── static/css, static/js, static/images
├── database/schema.sql
├── scripts/seed_demo.py, offline_verify.py, package_release.py
├── tests/conftest.py, test_workflows.py
├── docs/ (architecture, modules, design, security, test report)
└── instance/.gitkeep
```

## Troubleshooting

- `No module named flask`: Activate the venv and rerun `python -m pip install -r requirements.txt`.
- VS Code is using a different Python: `Ctrl+Shift+P` → `Python: Select Interpreter` → select `.venv`.
- Login rejected: Use the ID used at registration and the correct password; new students may still need approval to cast ballots.
- `Address already in use`: Stop another local process using port 5000.
- Dark mode: Use the top-bar sun/moon icon. Preference is stored in that browser only.
- Empty dashboard: Real data is intentionally empty until students and elections are created, or the optional fictional demo seed is loaded.

## Tests & current verification status

See `docs/TEST_REPORT.md` for exactly what was run in the authoring environment. In particular, **full Flask route tests were provided but could not be executed during creation because the environment did not have Flask installed and network access to fetch it was unavailable.** This is not presented as a fully verified deployment.

## Project references

The pasted master specification named two PDF reference documents. Those PDFs were not present in the attached files for this UI request. The implemented screens follow the supplied screenshot and the detailed text specification; PDF-only requirements could not be cross-checked.
