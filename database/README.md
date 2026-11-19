# SQLite schema

The app automatically creates the seven tables from `schema.sql` when initialized. The database lives in the private `instance/` directory. All connections enable foreign-key checking and a busy timeout. The participation table uses `(election_id, user_id)` as its composite primary key; the ballots table stores a candidate and election but no user identity.

**Do not delete or reset a real database without a secure backup.**
