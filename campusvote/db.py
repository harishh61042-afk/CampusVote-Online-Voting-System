"""SQLite access and shared election-time rules."""
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from flask import current_app, g


def now_utc():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def connect(path):
    con = sqlite3.connect(str(path), timeout=15, isolation_level=None)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys = ON')
    con.execute('PRAGMA busy_timeout = 15000')
    return con


def get_db():
    if 'db' not in g:
        g.db = connect(current_app.config['DATABASE'])
    return g.db


def close_db(_exception=None):
    con = g.pop('db', None)
    if con is not None:
        con.close()


def init_schema(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    schema = Path(__file__).resolve().parent.parent / 'database' / 'schema.sql'
    con = connect(path)
    try:
        con.executescript(schema.read_text(encoding='utf-8'))
    finally:
        con.close()


def election_state(e, clock=None):
    """Derive displayed state; voting permission also checks state inside BEGIN IMMEDIATE."""
    state = e['status']
    clock = clock or now_utc()
    if state in ('draft', 'published', 'closed'):
        return state
    if clock < e['starts_at']:
        return 'scheduled'
    if clock >= e['ends_at']:
        return 'closed'
    return 'open'


def write_audit(con, actor_id, event, resource):
    con.execute('INSERT INTO audit_logs(actor_id,event_type,resource,created_at) VALUES(?,?,?,?)',
                (actor_id, event, resource, now_utc()))
