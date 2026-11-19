# 7-minute demonstration walkthrough

1. Open the landing page. Explain the app is an academic Python/Flask/SQLite prototype with white/mint dashboard UI (30 sec).
2. Log in as admin created with `flask --app run.py create-admin`. Show total registered, approvals, participation gauge and recent elections (45 sec).
3. In Student Verification, approve a *pending* demo student; show the updated status (45 sec).
4. In Elections, create a draft. Add two candidate cards and select approved voters. Finalize and schedule. Or use the seeded open election to demonstrate immediately (1 min).
5. Log out and log in as `STU001` using the generated demo password. Show My Elections and candidate manifestos (45 sec).
6. Select a candidate, click Review my vote, explain the irreversible confirmation, and submit (45 sec).
7. Show the neutral receipt — no candidate name. Try to submit again. Explain `BEGIN IMMEDIATE` and the participation composite key (1 min).
8. Show the preloaded published Cultural Committee election results. Explain turnout, zero-vote candidates, ties and the secrecy of live candidate totals (45 sec).
9. Return to admin to show audit logs and published aggregate CSV export (30 sec).

Use fictional data only. The demo seed password is printed in the local terminal and should not be embedded in slides, screenshots or public repositories.
