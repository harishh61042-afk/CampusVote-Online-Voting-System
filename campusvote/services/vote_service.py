"""Vote integrity is enforced inside one SQLite write transaction."""
import secrets
import sqlite3
from campusvote.db import now_utc, election_state


class VoteError(Exception):
    pass


def cast_vote(con, user_id, election_id, candidate_id, *, fail_after_participation=False):
    """Return neutral receipt or raise VoteError. Never store student -> candidate mapping.

    Callers must validate CSRF/auth before invoking. BEGIN IMMEDIATE serializes
    competing writers from separate connections and unique PK rejects repeats.
    """
    receipt = secrets.token_urlsafe(20)
    try:
        con.execute('BEGIN IMMEDIATE')
        voter = con.execute('SELECT role,approval_status FROM users WHERE id=?', (user_id,)).fetchone()
        election = con.execute('SELECT * FROM elections WHERE id=?', (election_id,)).fetchone()
        candidate = con.execute('SELECT id FROM candidates WHERE id=? AND election_id=?',
                                (candidate_id, election_id)).fetchone()
        eligible = con.execute('SELECT 1 FROM eligibility WHERE election_id=? AND user_id=?',
                               (election_id, user_id)).fetchone()
        prior = con.execute('SELECT 1 FROM participation WHERE election_id=? AND user_id=?',
                            (election_id, user_id)).fetchone()
        if not voter or voter['role'] != 'student' or voter['approval_status'] != 'approved':
            raise VoteError('Your account is not approved for voting.')
        if not election or election_state(election) != 'open':
            raise VoteError('This election is not open for voting.')
        if not eligible:
            raise VoteError('You are not eligible for this election.')
        if not candidate:
            raise VoteError('Please select a valid candidate for this election.')
        if prior:
            raise VoteError('You have already voted in this election.')
        stamp = now_utc()
        con.execute('INSERT INTO participation(election_id,user_id,receipt,cast_at) VALUES(?,?,?,?)',
                    (election_id, user_id, receipt, stamp))
        if fail_after_participation:
            raise sqlite3.OperationalError('Injected failure for rollback verification')
        con.execute('INSERT INTO ballots(election_id,candidate_id,cast_at) VALUES(?,?,?)',
                    (election_id, candidate_id, stamp))
        con.execute('COMMIT')
        return receipt
    except VoteError:
        con.execute('ROLLBACK')
        raise
    except sqlite3.IntegrityError:
        con.execute('ROLLBACK')
        raise VoteError('This vote could not be accepted. You may already have voted.') from None
    except Exception:
        con.execute('ROLLBACK')
        raise
