"""Offline integrity tests without Flask installed; uses actual project service functions.
Run: python scripts/offline_verify.py
"""
import ast
from datetime import datetime,timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from types import ModuleType
import importlib.util
import sqlite3
import sys
import tempfile
import threading

ROOT=Path(__file__).resolve().parent.parent
SRC=ROOT/'campusvote'


def load_nonflask_modules():
    # Extract selected pure DB functions from db.py without importing Flask.
    source=(SRC/'db.py').read_text()
    tree=ast.parse(source)
    names={'now_utc','connect','init_schema','election_state','write_audit'}
    functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    ns={'datetime':datetime,'timezone':timezone,'Path':Path,'sqlite3':sqlite3,'__file__':str(SRC/'db.py')}
    exec(compile(ast.Module(body=functions,type_ignores=[]),str(SRC/'db.py'),'exec'),ns)
    pkg=ModuleType('campusvote');pkg.__path__=[str(SRC)]
    services=ModuleType('campusvote.services');services.__path__=[str(SRC/'services')]
    db=ModuleType('campusvote.db')
    for name in names:setattr(db,name,ns[name])
    sys.modules.update({'campusvote':pkg,'campusvote.services':services,'campusvote.db':db})
    result={}
    for name in ('vote_service','result_service'):
        spec=importlib.util.spec_from_file_location('campusvote.services.'+name,SRC/'services'/(name+'.py'))
        mod=importlib.util.module_from_spec(spec)
        sys.modules[spec.name]=mod
        spec.loader.exec_module(mod)
        result[name]=mod
    return ns,result


def verify():
    for path in ROOT.rglob('*.py'):
        compile(path.read_bytes(),str(path),'exec')
    print('PASS: Python source syntax')
    ns,modules=load_nonflask_modules();cast=modules['vote_service'].cast_vote;VoteError=modules['vote_service'].VoteError
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)/'test.sqlite3';ns['init_schema'](path)
        db=ns['connect'](path)
        names={row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {'users','elections','candidates','eligibility','participation','ballots','audit_logs'}.issubset(names)
        assert db.execute('PRAGMA foreign_keys').fetchone()[0]==1
        print('PASS: Seven SQLite tables and foreign keys')
        ts=ns['now_utc']();uid=[]
        for n,status in [(1,'approved'),(2,'approved'),(3,'pending')]:
            uid.append(db.execute('INSERT INTO users(student_id,full_name,password_hash,role,approval_status,created_at) VALUES(?,?,?,?,?,?)',
                   (f'STU{n}','Fictional Student','hashed-for-storage-test','student',status,ts)).lastrowid)
        admin=db.execute('INSERT INTO users(student_id,full_name,password_hash,role,approval_status,created_at) VALUES(?,?,?,?,?,?)',
                   ('ADMIN','Admin','hashed-for-storage-test','admin','approved',ts)).lastrowid
        e=db.execute('INSERT INTO elections(title,starts_at,ends_at,status,created_by,created_at) VALUES(?,?,?,?,?,?)',
               ('Test Election','2025-01-01T00:00:00Z','2028-01-01T00:00:00Z','scheduled',admin,ts)).lastrowid
        other=db.execute('INSERT INTO elections(title,starts_at,ends_at,status,created_by,created_at) VALUES(?,?,?,?,?,?)',
               ('Other Election','2027-01-01T00:00:00Z','2027-01-02T00:00:00Z','scheduled',admin,ts)).lastrowid
        c1=db.execute('INSERT INTO candidates(election_id,full_name,created_at) VALUES(?,?,?)',(e,'Candidate A',ts)).lastrowid
        c2=db.execute('INSERT INTO candidates(election_id,full_name,created_at) VALUES(?,?,?)',(e,'Candidate B',ts)).lastrowid
        other_candidate=db.execute('INSERT INTO candidates(election_id,full_name,created_at) VALUES(?,?,?)',(other,'Other',ts)).lastrowid
        for u in uid:db.execute('INSERT INTO eligibility(election_id,user_id) VALUES(?,?)',(e,u))
        db.close()
        try:
            con=ns['connect'](path)
            cast(con,uid[2],e,c1)
            raise AssertionError('Pending voter accepted')
        except VoteError:pass
        finally:con.close()
        print('PASS: Pending voter cannot vote')
        for eid,cid in [(e,other_candidate),(other,other_candidate)]:
            con=ns['connect'](path)
            try:
                cast(con,uid[0],eid,cid)
                raise AssertionError('Wrong candidate or closed election accepted')
            except VoteError:pass
            finally:con.close()
        print('PASS: Invalid candidate and out-of-window election rejected')
        con=ns['connect'](path)
        try:
            cast(con,uid[0],e,c1,fail_after_participation=True)
            raise AssertionError('Injected failure should raise')
        except sqlite3.OperationalError:pass
        assert con.execute('SELECT COUNT(*) FROM participation').fetchone()[0]==0
        assert con.execute('SELECT COUNT(*) FROM ballots').fetchone()[0]==0
        con.close();print('PASS: Failed transaction rolls back participation and ballot')
        gate=threading.Barrier(2)
        def vote_once():
            local=ns['connect'](path)
            try:
                gate.wait(timeout=5)
                return cast(local,uid[0],e,c1)
            except VoteError:return 'blocked'
            finally:local.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            f1=pool.submit(vote_once);f2=pool.submit(vote_once)
            outcome=[f1.result(timeout=20),f2.result(timeout=20)]
        assert outcome.count('blocked')==1
        db=ns['connect'](path)
        assert db.execute('SELECT COUNT(*) FROM participation').fetchone()[0]==1
        assert db.execute('SELECT COUNT(*) FROM ballots').fetchone()[0]==1
        print('PASS: Concurrent separate-connection requests accept exactly one ballot')
        assert modules['result_service'].published_results(db,e) is None
        db.execute("UPDATE elections SET status='published' WHERE id=?",(e,))
        stats=modules['result_service'].published_results(db,e)
        assert stats['total']==1 and stats['candidates'][1]['votes']==0
        print('PASS: Unpublished results concealed; published zero-vote candidates included')
        assert db.execute('SELECT COUNT(*) FROM ballots').fetchone()[0]==1
        db.close()
    print('OFFLINE CHECKS PASSED (not a substitute for Flask route tests).')

if __name__=='__main__':verify()
