# System architecture

```text
Browser (HTML, CSS, Vanilla JS)
            │ HTTPS on real deployments; localhost HTTP for the demo
            ▼
Flask factory + three blueprints
  ├─ auth: registration, login, logout, profile
  ├─ admin: approvals, elections, candidates, eligibility, audit, CSV
  └─ voting: student dashboard, ballots, receipts, published results
            │
            ├─ vote_service.py: BEGIN IMMEDIATE, constraints, neutral receipt
            ├─ result_service.py: aggregate statistics, ties and zero-vote rows
            ▼
SQLite database in private instance/ directory
```

All mutating forms contain a local per-session CSRF token verified by Flask. Protected endpoints check the authenticated user and role on the server. Templates are Jinja2 with auto-escaping. UI charts use CSS and data queried from SQLite; no browser API and no external JS/chart package is needed.

Election lifecycle: draft; scheduled; currently open when the UTC server clock is between stored start/end times; closed when explicitly closed or time expires; published after an administrator action. The application stores UTC but presents dates as IST for its student audience.
