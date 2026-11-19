"""Student dashboard, voting, neutral receipts and published results."""
from flask import Blueprint, request, render_template, redirect, url_for, flash, g, abort
from campusvote import role_required, login_required
from campusvote.db import get_db, election_state
from campusvote.services.vote_service import cast_vote, VoteError
from campusvote.services.result_service import published_results

bp=Blueprint('voting',__name__)


@bp.get('/dashboard')
@role_required('student')
def dashboard():
    db=get_db(); uid=g.user['id']
    rows=db.execute('''SELECT e.*,p.receipt,p.cast_at,
       (SELECT COUNT(*) FROM candidates WHERE election_id=e.id) AS candidate_count
       FROM elections e JOIN eligibility x ON x.election_id=e.id AND x.user_id=?
       LEFT JOIN participation p ON p.election_id=e.id AND p.user_id=?
       ORDER BY e.starts_at DESC''',(uid,uid)).fetchall()
    elections=[{**dict(r),'state':election_state(r)} for r in rows]
    stats={'total':len(elections), 'open':sum(e['state']=='open' for e in elections),
           'voted':sum(bool(e['receipt']) for e in elections),
           'upcoming':sum(e['state']=='scheduled' for e in elections)}
    published=db.execute("SELECT * FROM elections WHERE status='published' ORDER BY ends_at DESC LIMIT 4").fetchall()
    return render_template('student/dashboard.html',page='dashboard',elections=elections,stats=stats,published=published)


@bp.get('/my-elections')
@role_required('student')
def elections():
    db=get_db(); uid=g.user['id']
    q=request.args.get('q','').strip()[:80]
    rows=db.execute('''SELECT e.*, p.receipt FROM elections e
       JOIN eligibility x ON x.election_id=e.id AND x.user_id=?
       LEFT JOIN participation p ON p.election_id=e.id AND p.user_id=?
       WHERE e.title LIKE ? ORDER BY e.starts_at DESC''',(uid,uid,'%'+q+'%')).fetchall()
    return render_template('student/elections.html',page='elections',elections=rows)


@bp.get('/vote/<int:election_id>')
@role_required('student')
def vote_page(election_id):
    db=get_db();e=db.execute('''SELECT e.*,p.receipt FROM elections e
       JOIN eligibility x ON x.election_id=e.id AND x.user_id=?
       LEFT JOIN participation p ON p.election_id=e.id AND p.user_id=?
       WHERE e.id=?''',(g.user['id'],g.user['id'],election_id)).fetchone()
    if not e:abort(404)
    candidates=db.execute('SELECT * FROM candidates WHERE election_id=? ORDER BY full_name',(election_id,)).fetchall()
    return render_template('student/vote.html',page='elections',e=e,state=election_state(e),candidates=candidates)


@bp.post('/vote/<int:election_id>')
@role_required('student')
def submit_vote(election_id):
    try: candidate_id=int(request.form.get('candidate_id',''))
    except ValueError:
        flash('Select one candidate before submitting.','error')
        return redirect(url_for('voting.vote_page',election_id=election_id))
    try:
        receipt=cast_vote(get_db(),g.user['id'],election_id,candidate_id)
    except VoteError as err:
        flash(str(err),'error')
        return redirect(url_for('voting.vote_page',election_id=election_id))
    return redirect(url_for('voting.receipt',receipt=receipt))


@bp.get('/receipt/<receipt>')
@role_required('student')
def receipt(receipt):
    row=get_db().execute('''SELECT p.receipt,p.cast_at,e.title FROM participation p
       JOIN elections e ON e.id=p.election_id WHERE p.receipt=? AND p.user_id=?''',(receipt,g.user['id'])).fetchone()
    if not row:abort(404)
    return render_template('student/receipt.html',page='elections',row=row)


@bp.get('/results')
@login_required
def results_list():
    rows=get_db().execute("SELECT * FROM elections WHERE status='published' ORDER BY ends_at DESC").fetchall()
    return render_template('results/list.html',page='results',elections=rows)


@bp.get('/results/<int:election_id>')
@login_required
def results(election_id):
    result=published_results(get_db(),election_id)
    if result is None: abort(403,description='Results have not been published yet.')
    return render_template('results/detail.html',page='results',result=result)
