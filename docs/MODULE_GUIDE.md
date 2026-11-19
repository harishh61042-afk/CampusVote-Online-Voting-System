# Ten modules for the RTRP viva

1. **Student Registration** — Students create an account with a unique ID. Passwords are hashed. New voters are pending.
2. **Authentication & Profile** — Flask sessions identify users; login/logout and password change are supported.
3. **Student Verification** — An admin approves or rejects pending registrations and can search the directory.
4. **Election Management** — The admin creates draft elections, edits the schedule, selects eligible voters, and manages the election lifecycle.
5. **Candidate Management** — The admin adds, edits and deletes candidate profiles while the election is in draft.
6. **Vote Casting** — An approved student views assigned elections, selects one candidate, reviews a dialog and submits once.
7. **Vote Integrity** — SQLite validates approvals, election timing, candidate, eligibility and duplicates in an atomic write transaction.
8. **Results** — Candidate votes, percentages, tie winners and turnout are computed from real database records, shown only after publication.
9. **Role-Based Dashboards** — Students see their ballots/status; administrators see safe participation metrics, verification queue and activity.
10. **Audit & Reporting** — The system stores administrative changes and allows published, aggregate-only CSV exports.

**Viva answer:** `BEGIN IMMEDIATE` plus `PRIMARY KEY(election_id,user_id)` is used to stop duplicate voting even if two requests arrive together. CSS/JS makes the experience polished; the Python backend, not JavaScript, guarantees eligibility and one-vote rules.
