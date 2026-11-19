# Database design

- **users**: PK `id`; unique `student_id`; hashed password; role student/admin; approval pending/approved/rejected.
- **elections**: PK `id`; title/description; UTC start/end; `status` draft/scheduled/closed/published; `created_by` FK users.
- **candidates**: PK `id`; `election_id` FK elections; full name, department, manifesto; unique `(id,election_id)` composite referenced by ballots.
- **eligibility**: PK `(election_id,user_id)`; both columns FKs; frozen after draft.
- **participation**: PK `(election_id,user_id)`; unique random receipt and timestamp; no candidate ID.
- **ballots**: PK `id`; `(candidate_id,election_id)` composite FK candidates; timestamp; **no user ID**.
- **audit_logs**: PK `id`; actor user FK, event, affected resource, timestamp; never stores a chosen candidate or ballot contents.

SQLite always uses `PRAGMA foreign_keys=ON`. Vote service obtains a write lock via `BEGIN IMMEDIATE` and inserts participation and ballot as one transaction. It either commits both or rolls both back. Even concurrent separate connections cannot accept two participation records for the same student and election.

The separation of the tables reduces obvious voter/choice linkage but **does not guarantee cryptographic anonymity**. A database administrator can examine submission sequence, transaction timing, backups or logs. This is an educational prototype, not a certified end-to-end verifiable voting protocol.
