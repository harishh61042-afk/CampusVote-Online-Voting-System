"""Optional, disposable fictional demo seed. Never runs on normal app startup."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import secrets
import random
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from werkzeug.security import generate_password_hash
from campusvote import create_app
from campusvote.db import get_db, now_utc

names=['Ava Mitchell','Ethan Clarke','Liam Parker','Sophia Hayes','Noah Bennett',
       'Mia Carter','Oliver James','Emma Brooks','Lucas Morgan','Isabella Reed',
       'Arjun Mehta','Zara Khan','Ryan Walker','Ella Price','Aiden Cole']
app=create_app()

def utc(offset):
    return (datetime.now(timezone.utc)+timedelta(hours=offset)).strftime('%Y-%m-%dT%H:%M:%SZ')

with app.app_context():
    db=get_db()
    admin=db.execute("SELECT id FROM users WHERE role='admin' ORDER BY id LIMIT 1").fetchone()
    if not admin:
        print('Create an administrator first with: flask --app run.py create-admin')
        sys.exit(1)
    if db.execute("SELECT 1 FROM users WHERE student_id='STU001'").fetchone():
        print('Demo student IDs already exist; no data was changed. Use a fresh local database for a clean demo.')
        sys.exit(0)
    demo_password=secrets.token_urlsafe(14)
    rnd=random.Random(42)
    try:
        db.execute('BEGIN IMMEDIATE')
        voters=[]
        for i,name in enumerate(names,1):
            status='approved' if i<=11 else ('pending' if i<=13 else 'rejected')
            uid=db.execute('INSERT INTO users(student_id,full_name,email,password_hash,role,approval_status,created_at) VALUES(?,?,?,?,?,?,?)',
                           (f'STU{i:03}',name,None,generate_password_hash(demo_password),'student',status,now_utc())).lastrowid
            if status=='approved':voters.append(uid)
        election_defs=[
          ('Student Council Election','Choose the next student council representative.',utc(-2),utc(48),'scheduled'),
          ('Tech Club Leadership','Vote for the leadership of the campus technology club.',utc(72),utc(120),'scheduled'),
          ('Cultural Committee 2026','Annual cultural committee election.',utc(-240),utc(-216),'published'),
        ]
        for idx,(title,desc,start,end,status) in enumerate(election_defs):
            election_id=db.execute('INSERT INTO elections(title,description,starts_at,ends_at,status,created_by,created_at) VALUES(?,?,?,?,?,?,?)',
                                   (title,desc,start,end,status,admin['id'],now_utc())).lastrowid
            cid=[]
            for j,(name,department,manifesto) in enumerate([
                ('Riya Sharma','CSE · 3rd Year','Transparent campus events and stronger student support.'),
                ('Karan Patel','ECE · 3rd Year','More clubs, academic support, and accessible facilities.'),
                ('Neha Rao','IT · 2nd Year','Better communication and opportunities for all students.'),
            ]):
                cid.append(db.execute('INSERT INTO candidates(election_id,full_name,department,manifesto,created_at) VALUES(?,?,?,?,?)',
                                      (election_id,name,department,manifesto,now_utc())).lastrowid)
            for uid in voters:
                db.execute('INSERT INTO eligibility(election_id,user_id) VALUES(?,?)',(election_id,uid))
            if idx==2:
                for uid in voters[:9]:
                    db.execute('INSERT INTO participation(election_id,user_id,receipt,cast_at) VALUES(?,?,?,?)',
                               (election_id,uid,secrets.token_urlsafe(20),utc(-228)))
                    db.execute('INSERT INTO ballots(election_id,candidate_id,cast_at) VALUES(?,?,?)',
                               (election_id,rnd.choice(cid),utc(-228)))
        db.execute('COMMIT')
    except Exception:
        db.execute('ROLLBACK')
        raise
    print('Fictional demo data created (15 students, 3 elections).')
    print('Approved demo voter ID: STU001')
    print('Demo voter password:',demo_password)
    print('This is for local demonstration only. Never reuse this password for real data.')
