"""End-to-end Flask test client workflows; external providers are not needed."""
from datetime import datetime,timezone,timedelta
import sqlite3
import threading
from campusvote.db import connect, now_utc
from campusvote.services.vote_service import cast_vote, VoteError
from campusvote.services.result_service import published_results
from conftest import csrf, sign_in


def test_home_login_registration_and_duplicate(client,db):
    assert client.get('/').status_code==200
    client.get('/register')
    form={'full_name':'New Student','student_id':'ABC123','email':'new@college.edu',
          'password':'GoodPassword123','confirm_password':'GoodPassword123','terms':'yes','csrf_token':csrf(client)}
    assert client.post('/register',data=form).status_code==302
    assert client.post('/register',data=form,follow_redirects=True).status_code==200
    assert db.execute("SELECT COUNT(*) FROM users WHERE student_id='ABC123'").fetchone()[0]==1
    assert db.execute("SELECT approval_status FROM users WHERE student_id='ABC123'").fetchone()[0]=='pending'
    assert db.execute("SELECT password_hash FROM users WHERE student_id='ABC123'").fetchone()[0]!='GoodPassword123'


def test_invalid_credentials_and_csrf(client,actors):
    client.get('/login')
    r=client.post('/login',data={'student_id':'STU001','password':'incorrect','csrf_token':csrf(client)})
    assert b'Invalid ID or password' in r.data
    assert client.post('/register',data={'student_id':'ZZZ123'}).status_code==400


def test_pending_cannot_vote(db,actors,election):
    db.execute('INSERT INTO eligibility(election_id,user_id) VALUES(?,?)',(election['id'],actors['STU003']))
    try:cast_vote(db,actors['STU003'],election['id'],election['c1'])
    except VoteError as exc:assert 'not approved' in str(exc)
    else:assert False,'pending voter accepted'


def test_one_vote_and_neutral_receipt(client,db,actors,election):
    sign_in(client)
    assert client.get('/vote/'+str(election['id'])).status_code==200
    form={'candidate_id':election['c1'],'csrf_token':csrf(client)}
    response=client.post('/vote/'+str(election['id']),data=form)
    assert response.status_code==302 and '/receipt/' in response.location
    receipt=client.get(response.location)
    assert receipt.status_code==200
    assert b'Candidate Alpha' not in receipt.data and b'Candidate Beta' not in receipt.data
    assert client.post('/vote/'+str(election['id']),data=form).status_code==302
    assert db.execute('SELECT COUNT(*) FROM participation').fetchone()[0]==1
    assert db.execute('SELECT COUNT(*) FROM ballots').fetchone()[0]==1


def test_wrong_candidate_other_election_and_timing(db,actors,election):
    from campusvote.services.vote_service import VoteError
    new=db.execute('INSERT INTO elections(title,starts_at,ends_at,status,created_by,created_at) VALUES(?,?,?,?,?,?)',
        ('Other Election','2027-01-01T00:00:00Z','2027-01-02T00:00:00Z','scheduled',actors['ADM001'],now_utc())).lastrowid
    other_candidate=db.execute('INSERT INTO candidates(election_id,full_name,created_at) VALUES(?,?,?)',(new,'Other',now_utc())).lastrowid
    for eid,cid in [(election['id'],other_candidate),(new,other_candidate)]:
        try:cast_vote(db,actors['STU001'],eid,cid)
        except VoteError:pass
        else:assert False,'invalid ballot accepted'
    assert db.execute('SELECT COUNT(*) FROM ballots').fetchone()[0]==0


def test_concurrent_writes_accept_one(app,actors,election):
    barrier=threading.Barrier(2)
    results=[]
    def worker():
        con=connect(app.config['DATABASE']);barrier.wait()
        try: results.append(cast_vote(con,actors['STU001'],election['id'],election['c1']))
        except VoteError:results.append('blocked')
        finally:con.close()
    a=threading.Thread(target=worker);b=threading.Thread(target=worker)
    a.start();b.start();a.join(timeout=15);b.join(timeout=15)
    assert not a.is_alive() and not b.is_alive()
    assert len(results)==2 and results.count('blocked')==1
    con=connect(app.config['DATABASE'])
    assert con.execute('SELECT COUNT(*) FROM ballots').fetchone()[0]==1
    assert con.execute('SELECT COUNT(*) FROM participation').fetchone()[0]==1
    con.close()


def test_rollback(db,actors,election):
    try:cast_vote(db,actors['STU001'],election['id'],election['c1'],fail_after_participation=True)
    except sqlite3.OperationalError:pass
    else:assert False,'injected failure did not propagate'
    assert db.execute('SELECT COUNT(*) FROM participation').fetchone()[0]==0
    assert db.execute('SELECT COUNT(*) FROM ballots').fetchone()[0]==0


def test_publication_visibility_zero_votes_ties(db,actors,election,client):
    assert published_results(db,election['id']) is None
    sign_in(client)
    assert client.get('/results/'+str(election['id'])).status_code==403
    db.execute("UPDATE elections SET status='closed' WHERE id=?",(election['id'],))
    assert published_results(db,election['id']) is None
    db.execute("UPDATE elections SET status='published' WHERE id=?",(election['id'],))
    result=published_results(db,election['id'])
    assert result['total']==0 and all(c['votes']==0 for c in result['candidates'])
    for user,candidate in [(actors['STU001'],election['c1']),(actors['STU002'],election['c2'])]:
        db.execute('INSERT INTO participation(election_id,user_id,receipt,cast_at) VALUES(?,?,?,?)',(election['id'],user,'receipt'+str(user),now_utc()))
        db.execute('INSERT INTO ballots(election_id,candidate_id,cast_at) VALUES(?,?,?)',(election['id'],candidate,now_utc()))
    result=published_results(db,election['id'])
    assert len(result['leaders'])==2 and result['total']==2
    assert client.get('/results/'+str(election['id'])).status_code==200


def test_student_admin_forbidden_and_escaping(client,actors,election,db):
    sign_in(client)
    assert client.get('/admin/dashboard').status_code==403
    assert client.get('/admin/students').status_code==403
    assert client.post('/admin/elections/1/action',data={'csrf_token':csrf(client),'action':'publish'}).status_code==403
    db.execute("UPDATE elections SET title=? WHERE id=?",('<script>alert(1)</script>',election['id']))
    html=client.get('/my-elections').data
    assert b'<script>alert(1)</script>' not in html
    assert b'&lt;script&gt;' in html


def test_admin_approval_and_lifecycle(client,db,actors,election):
    sign_in(client,'ADM001')
    r=client.post('/admin/students/'+str(actors['STU003'])+'/decision',data={'csrf_token':csrf(client),'decision':'approved'})
    assert r.status_code==302
    assert db.execute('SELECT approval_status FROM users WHERE id=?',(actors['STU003'],)).fetchone()[0]=='approved'
    assert client.post('/admin/elections/'+str(election['id'])+'/action',data={'csrf_token':csrf(client),'action':'publish'}).status_code==400
    assert client.get('/admin/reports/'+str(election['id'])+'/export.csv').status_code==403
    assert client.get('/admin/audit').status_code==200


def test_receipt_ownership(client,db,actors,election):
    receipt=cast_vote(db,actors['STU001'],election['id'],election['c1'])
    sign_in(client,'STU002')
    assert client.get('/receipt/'+receipt).status_code==404


def test_password_change_and_logout(client,actors):
    sign_in(client)
    token=csrf(client)
    result=client.post('/profile',data={'old_password':'Testpass123!','new_password':'NewPass9999!',
                                        'confirm_password':'NewPass9999!','csrf_token':token})
    assert result.status_code==302
    assert client.post('/logout',data={'csrf_token':csrf(client)}).status_code==302
    assert client.get('/dashboard').status_code==302
