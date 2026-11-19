PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 student_id TEXT NOT NULL UNIQUE,
 full_name TEXT NOT NULL,
 email TEXT,
 password_hash TEXT NOT NULL,
 role TEXT NOT NULL DEFAULT 'student' CHECK(role IN ('student','admin')),
 approval_status TEXT NOT NULL DEFAULT 'pending' CHECK(approval_status IN ('pending','approved','rejected')),
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS elections (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 title TEXT NOT NULL,
 description TEXT NOT NULL DEFAULT '',
 starts_at TEXT NOT NULL,
 ends_at TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','scheduled','closed','published')),
 created_by INTEGER NOT NULL REFERENCES users(id),
 created_at TEXT NOT NULL,
 CHECK(starts_at < ends_at)
);
CREATE TABLE IF NOT EXISTS candidates (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 election_id INTEGER NOT NULL REFERENCES elections(id) ON DELETE RESTRICT,
 full_name TEXT NOT NULL,
 department TEXT NOT NULL DEFAULT '',
 manifesto TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL,
 UNIQUE(id, election_id)
);
CREATE TABLE IF NOT EXISTS eligibility (
 election_id INTEGER NOT NULL REFERENCES elections(id) ON DELETE RESTRICT,
 user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
 PRIMARY KEY(election_id, user_id)
);
CREATE TABLE IF NOT EXISTS participation (
 election_id INTEGER NOT NULL REFERENCES elections(id) ON DELETE RESTRICT,
 user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
 receipt TEXT NOT NULL UNIQUE,
 cast_at TEXT NOT NULL,
 PRIMARY KEY(election_id, user_id)
);
CREATE TABLE IF NOT EXISTS ballots (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 election_id INTEGER NOT NULL,
 candidate_id INTEGER NOT NULL,
 cast_at TEXT NOT NULL,
 FOREIGN KEY(candidate_id, election_id) REFERENCES candidates(id, election_id) ON DELETE RESTRICT
);
CREATE TABLE IF NOT EXISTS audit_logs (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 actor_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
 event_type TEXT NOT NULL,
 resource TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_eligible_user ON eligibility(user_id);
CREATE INDEX IF NOT EXISTS idx_ballots_election ON ballots(election_id);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_elections_status ON elections(status);
