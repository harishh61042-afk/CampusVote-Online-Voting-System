"""Flask functional tests, executed after installing requirements.txt."""
from datetime import datetime, timezone, timedelta
import pytest
from werkzeug.security import generate_password_hash
from campusvote import create_app
from campusvote.db import connect, now_utc

@pytest.fixture
def app(tmp_path):
    app=create_app({'TESTING':True,'SECRET_KEY':'test-only-secret-not-for-production','DATABASE':str(tmp_path/'test.sqlite3')})
    yield app

@pytest.fixture
def db(app):
    con=connect(app.config['DATABASE'])
    yield con
    con.close()

@pytest.fixture
def client(app):return app.test_client()

@pytest.fixture
def actors(db):
    people={}
    for sid,name,role,status in [('ADM001','Test Admin','admin','approved'),('STU001','Voter One','student','approved'),
                                 ('STU002','Voter Two','student','approved'),('STU003','Pending Voter','student','pending')]:
        c=db.execute('INSERT INTO users(student_id,full_name,password_hash,role,approval_status,created_at) VALUES(?,?,?,?,?,?)',
                      (sid,name,generate_password_hash('Testpass123!'),role,status,now_utc()))
        people[sid]=c.lastrowid
    return people

@pytest.fixture
def election(db,actors):
    now=datetime.now(timezone.utc)
    fmt=lambda dt:dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    row=db.execute('INSERT INTO elections(title,description,starts_at,ends_at,status,created_by,created_at) VALUES(?,?,?,?,?,?,?)',
                   ('Test Council','Simple election',fmt(now-timedelta(hours=2)),fmt(now+timedelta(hours=2)),
                    'scheduled',actors['ADM001'],now_utc()))
    e=row.lastrowid
    c1=db.execute('INSERT INTO candidates(election_id,full_name,created_at) VALUES(?,?,?)',(e,'Candidate Alpha',now_utc())).lastrowid
    c2=db.execute('INSERT INTO candidates(election_id,full_name,created_at) VALUES(?,?,?)',(e,'Candidate Beta',now_utc())).lastrowid
    for s in ('STU001','STU002'):
        db.execute('INSERT INTO eligibility(election_id,user_id) VALUES(?,?)',(e,actors[s]))
    return {'id':e,'c1':c1,'c2':c2}


def csrf(client):
    with client.session_transaction() as session:
        if '_csrf' not in session:
            client.get('/login')
    with client.session_transaction() as session:return session['_csrf']


def sign_in(client,id='STU001'):
    client.get('/login')
    return client.post('/login',data={'student_id':id,'password':'Testpass123!','csrf_token':csrf(client)},follow_redirects=True)
