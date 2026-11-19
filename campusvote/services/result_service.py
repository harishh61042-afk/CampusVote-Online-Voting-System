"""Published results, aggregate turnout, and tie-safe winners."""
from campusvote.db import election_state


def election_stats(con, election_id):
    e = con.execute('SELECT * FROM elections WHERE id=?', (election_id,)).fetchone()
    if not e:
        return None
    eligible = con.execute('SELECT COUNT(*) FROM eligibility WHERE election_id=?', (election_id,)).fetchone()[0]
    voted = con.execute('SELECT COUNT(*) FROM participation WHERE election_id=?', (election_id,)).fetchone()[0]
    return {'election': e, 'state': election_state(e), 'eligible': eligible,
            'voted': voted, 'turnout': round(100 * voted / eligible, 1) if eligible else 0}


def published_results(con, election_id):
    stats = election_stats(con, election_id)
    if stats is None or stats['state'] != 'published':
        return None
    rows = con.execute('''SELECT c.id,c.full_name,c.department,c.manifesto,
        COUNT(b.id) AS votes FROM candidates c
        LEFT JOIN ballots b ON b.candidate_id=c.id AND b.election_id=c.election_id
        WHERE c.election_id=? GROUP BY c.id ORDER BY votes DESC,c.full_name''', (election_id,)).fetchall()
    total = sum(r['votes'] for r in rows)
    leaders = [r['full_name'] for r in rows if total and r['votes'] == rows[0]['votes']]
    return {**stats, 'total': total, 'leaders': leaders,
            'candidates': [{**dict(r), 'percent': round(r['votes'] * 100 / total, 1) if total else 0}
                           for r in rows]}
