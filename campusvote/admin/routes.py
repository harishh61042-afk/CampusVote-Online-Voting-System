"""Administrator-only management routes."""
import csv
from io import StringIO
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, render_template, redirect, url_for, flash, g, abort, Response
from campusvote import role_required
from campusvote.db import get_db, now_utc, election_state, write_audit
from campusvote.services.result_service import published_results, election_stats

bp = Blueprint('admin', __name__, url_prefix='/admin')
IST = timezone(timedelta(hours=5, minutes=30))


def parse_ist(value):
    return datetime.strptime(value,'%Y-%m-%dT%H:%M').replace(tzinfo=IST).astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


@bp.get('/dashboard')
@role_required('admin')
def dashboard():
    db=get_db()
    counts={
      'students':db.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0],
      'approved':db.execute("SELECT COUNT(*) FROM users WHERE role='student' AND approval_status='approved'").fetchone()[0],
      'pending':db.execute("SELECT COUNT(*) FROM users WHERE role='student' AND approval_status='pending'").fetchone()[0],
      'elections':db.execute('SELECT COUNT(*) FROM elections').fetchone()[0],
    }
    election_rows=db.execute('''SELECT e.*, (SELECT COUNT(*) FROM eligibility WHERE election_id=e.id) AS eligible,
        (SELECT COUNT(*) FROM participation WHERE election_id=e.id) AS cast_votes
        FROM elections e ORDER BY e.created_at DESC LIMIT 7''').fetchall()
    elections=[{**dict(e),'state':election_state(e), 'turnout':round(100*e['cast_votes']/e['eligible']) if e['eligible'] else 0} for e in election_rows]
    counts['open']=sum(election_state(e)=='open' for e in db.execute('SELECT * FROM elections').fetchall())
    counts['voted']=db.execute('SELECT COUNT(*) FROM participation').fetchone()[0]
    total_eligible=db.execute('SELECT COUNT(*) FROM eligibility').fetchone()[0]
    counts['turnout']=round(counts['voted']*100/total_eligible) if total_eligible else 0
    peak=max([e['cast_votes'] for e in elections],default=0)
    counts['chart_peak']=peak
    for e in elections: e['bar_height']=max(10, round(100*e['cast_votes']/peak)) if peak else 10
    activity=db.execute('''SELECT a.*,u.full_name actor FROM audit_logs a
        LEFT JOIN users u ON u.id=a.actor_id ORDER BY a.id DESC LIMIT 5''').fetchall()
    pending=db.execute("SELECT id,student_id,full_name,created_at FROM users WHERE approval_status='pending' AND role='student' ORDER BY id DESC LIMIT 5").fetchall()
    return render_template('admin/dashboard.html',page='dashboard',counts=counts,elections=elections,activity=activity,pending=pending)


@bp.get('/students')
@role_required('admin')
def students():
    search=request.args.get('q','').strip()[:80]
    status=request.args.get('status','all')
    query="SELECT * FROM users WHERE role='student'"
    args=[]
    if search:
        query+=" AND (full_name LIKE ? OR student_id LIKE ?)"
        args.extend(['%'+search+'%']*2)
    if status in ('pending','approved','rejected'):
        query+=' AND approval_status=?'; args.append(status)
    rows=get_db().execute(query+' ORDER BY id DESC',args).fetchall()
    return render_template('admin/students.html', page='students', students=rows, search=search, status=status)


@bp.post('/students/<int:user_id>/decision')
@role_required('admin')
def decide_student(user_id):
    decision=request.form.get('decision')
    if decision not in ('approved','rejected'): abort(400)
    db=get_db()
    # Only pending can be changed; approved voters remain stable across active elections.
    cur=db.execute("UPDATE users SET approval_status=? WHERE id=? AND role='student' AND approval_status='pending'",(decision,user_id))
    if cur.rowcount:
        write_audit(db,g.user['id'],'student_'+decision,f'user:{user_id}')
        flash('Student '+decision+'.','success')
    else: flash('Student not found or already reviewed.','warning')
    return redirect(url_for('admin.students'))


@bp.route('/elections',methods=['GET','POST'])
@role_required('admin')
def elections():
    db=get_db()
    if request.method=='POST':
        title=request.form.get('title','').strip()
        desc=request.form.get('description','').strip()
        try:
            starts=parse_ist(request.form.get('starts_at',''))
            ends=parse_ist(request.form.get('ends_at',''))
        except ValueError:
            flash('Select valid start and end dates.','error')
            return redirect(url_for('admin.elections'))
        if not (3<=len(title)<=120) or len(desc)>1000 or starts>=ends:
            flash('Enter a title and an end time after the start time.','error')
            return redirect(url_for('admin.elections'))
        row=db.execute('INSERT INTO elections(title,description,starts_at,ends_at,created_by,created_at) VALUES(?,?,?,?,?,?)',
                       (title,desc,starts,ends,g.user['id'],now_utc()))
        write_audit(db,g.user['id'],'election_created',f'election:{row.lastrowid}')
        flash('Draft election created. Add candidates and eligible students.','success')
        return redirect(url_for('admin.election_detail',election_id=row.lastrowid))
    rows=db.execute('''SELECT e.*, (SELECT COUNT(*) FROM candidates WHERE election_id=e.id) candidate_count,
       (SELECT COUNT(*) FROM eligibility WHERE election_id=e.id) eligible_count
       FROM elections e ORDER BY id DESC''').fetchall()
    return render_template('admin/elections.html',page='elections',elections=rows)


@bp.get('/elections/<int:election_id>')
@role_required('admin')
def election_detail(election_id):
    db=get_db()
    e=db.execute('SELECT * FROM elections WHERE id=?',(election_id,)).fetchone()
    if not e: abort(404)
    candidates=db.execute('SELECT * FROM candidates WHERE election_id=? ORDER BY id',(election_id,)).fetchall()
    approved=db.execute("SELECT id,student_id,full_name FROM users WHERE role='student' AND approval_status='approved' ORDER BY full_name").fetchall()
    selected={row[0] for row in db.execute('SELECT user_id FROM eligibility WHERE election_id=?',(election_id,)).fetchall()}
    stats=election_stats(db,election_id)
    return render_template('admin/election_detail.html',page='elections',e=e,candidates=candidates,
                           approved=approved,selected=selected,stats=stats)


@bp.post('/elections/<int:election_id>/edit')
@role_required('admin')
def edit_election(election_id):
    db=get_db();e=db.execute('SELECT * FROM elections WHERE id=?',(election_id,)).fetchone()
    if not e:abort(404)
    if e['status']!='draft':abort(403)
    title=request.form.get('title','').strip();desc=request.form.get('description','').strip()
    try:
        starts=parse_ist(request.form.get('starts_at',''))
        ends=parse_ist(request.form.get('ends_at',''))
    except ValueError:
        flash('Enter valid dates and times.','error')
        return redirect(url_for('admin.election_detail',election_id=election_id))
    if not(3<=len(title)<=120) or len(desc)>1000 or starts>=ends:
        flash('Please provide valid election details and time window.','error')
    else:
        db.execute('UPDATE elections SET title=?,description=?,starts_at=?,ends_at=? WHERE id=?',
                   (title,desc,starts,ends,election_id))
        write_audit(db,g.user['id'],'election_updated',f'election:{election_id}')
        flash('Draft election updated.','success')
    return redirect(url_for('admin.election_detail',election_id=election_id))


@bp.post('/elections/<int:election_id>/candidates/<int:candidate_id>/edit')
@role_required('admin')
def edit_candidate(election_id,candidate_id):
    db=get_db();e=db.execute('SELECT status FROM elections WHERE id=?',(election_id,)).fetchone()
    if not e:abort(404)
    if e['status']!='draft':abort(403)
    name=request.form.get('name','').strip();department=request.form.get('department','').strip()
    manifesto=request.form.get('manifesto','').strip()
    if not(2<=len(name)<=100) or len(department)>100 or len(manifesto)>1500:
        flash('Please enter valid candidate details.','error')
    else:
        cur=db.execute('UPDATE candidates SET full_name=?,department=?,manifesto=? WHERE id=? AND election_id=?',
                       (name,department,manifesto,candidate_id,election_id))
        if not cur.rowcount:abort(404)
        write_audit(db,g.user['id'],'candidate_updated',f'candidate:{candidate_id}')
        flash('Candidate updated.','success')
    return redirect(url_for('admin.election_detail',election_id=election_id))


@bp.post('/elections/<int:election_id>/candidate')
@role_required('admin')
def add_candidate(election_id):
    db=get_db();e=db.execute('SELECT * FROM elections WHERE id=?',(election_id,)).fetchone()
    if not e:abort(404)
    if e['status']!='draft':abort(403)
    name=request.form.get('name','').strip(); department=request.form.get('department','').strip(); manifesto=request.form.get('manifesto','').strip()
    if not (2<=len(name)<=100) or len(department)>100 or len(manifesto)>1500:
        flash('Enter a candidate name (2–100 characters) and shorter details.','error')
    else:
        row=db.execute('INSERT INTO candidates(election_id,full_name,department,manifesto,created_at) VALUES(?,?,?,?,?)',
                       (election_id,name,department,manifesto,now_utc()))
        write_audit(db,g.user['id'],'candidate_added',f'candidate:{row.lastrowid}')
        flash('Candidate added.','success')
    return redirect(url_for('admin.election_detail',election_id=election_id))


@bp.post('/elections/<int:election_id>/candidates/<int:candidate_id>/delete')
@role_required('admin')
def delete_candidate(election_id,candidate_id):
    db=get_db(); e=db.execute('SELECT status FROM elections WHERE id=?',(election_id,)).fetchone()
    if not e:abort(404)
    if e['status']!='draft':abort(403)
    cur=db.execute('DELETE FROM candidates WHERE id=? AND election_id=?',(candidate_id,election_id))
    if cur.rowcount:write_audit(db,g.user['id'],'candidate_removed',f'candidate:{candidate_id}')
    return redirect(url_for('admin.election_detail',election_id=election_id))


@bp.post('/elections/<int:election_id>/eligibility')
@role_required('admin')
def set_eligibility(election_id):
    db=get_db();e=db.execute('SELECT * FROM elections WHERE id=?',(election_id,)).fetchone()
    if not e:abort(404)
    if e['status']!='draft':abort(403)
    desired={int(s) for s in request.form.getlist('student_ids') if s.isdigit()}
    valid={r[0] for r in db.execute("SELECT id FROM users WHERE role='student' AND approval_status='approved'")}
    if not desired.issubset(valid):abort(400)
    try:
        db.execute('BEGIN IMMEDIATE')
        db.execute('DELETE FROM eligibility WHERE election_id=?',(election_id,))
        db.executemany('INSERT INTO eligibility(election_id,user_id) VALUES(?,?)',[(election_id,u) for u in sorted(desired)])
        write_audit(db,g.user['id'],'eligibility_updated',f'election:{election_id}')
        db.execute('COMMIT')
    except Exception:
        db.execute('ROLLBACK');raise
    flash('Eligible voters saved.','success')
    return redirect(url_for('admin.election_detail',election_id=election_id))


@bp.post('/elections/<int:election_id>/action')
@role_required('admin')
def election_action(election_id):
    db=get_db();e=db.execute('SELECT * FROM elections WHERE id=?',(election_id,)).fetchone()
    if not e:abort(404)
    action=request.form.get('action'); state=election_state(e)
    if action=='schedule' and state=='draft':
        nc=db.execute('SELECT COUNT(*) FROM candidates WHERE election_id=?',(election_id,)).fetchone()[0]
        nv=db.execute('SELECT COUNT(*) FROM eligibility WHERE election_id=?',(election_id,)).fetchone()[0]
        if nc<2 or nv<1:
            flash('Add at least two candidates and one eligible voter before scheduling.','error')
            return redirect(url_for('admin.election_detail',election_id=election_id))
        if e['ends_at']<=now_utc():
            flash('The election end time must be in the future. Create a new schedule.','error')
            return redirect(url_for('admin.election_detail',election_id=election_id))
        target='scheduled'
    elif action=='close' and state=='open':target='closed'
    elif action=='publish' and state=='closed':target='published'
    else:abort(400,description='That transition is not allowed.')
    db.execute('UPDATE elections SET status=? WHERE id=?',(target,election_id))
    write_audit(db,g.user['id'],'election_'+target,f'election:{election_id}')
    flash('Election status: '+target+'.','success')
    return redirect(url_for('admin.election_detail',election_id=election_id))


@bp.get('/audit')
@role_required('admin')
def audit():
    q=request.args.get('q','').strip()[:80]
    rows=get_db().execute('''SELECT a.*,u.full_name actor FROM audit_logs a
        LEFT JOIN users u ON u.id=a.actor_id WHERE event_type LIKE ? OR resource LIKE ?
        ORDER BY a.id DESC LIMIT 250''',('%'+q+'%','%'+q+'%')).fetchall()
    return render_template('admin/audit.html',page='audit',logs=rows,search=q)


@bp.get('/reports')
@role_required('admin')
def reports():
    rows=get_db().execute('SELECT * FROM elections ORDER BY id DESC').fetchall()
    return render_template('admin/reports.html',page='reports',elections=rows)


@bp.get('/reports/<int:election_id>/export.csv')
@role_required('admin')
def export_results(election_id):
    result=published_results(get_db(),election_id)
    if result is None:abort(403,description='Results can only be exported after publication.')
    output=StringIO();writer=csv.writer(output)
    writer.writerow(['Election','Candidate','Department','Votes','Percentage'])
    def safe_csv(text):
        value=str(text)
        return "'"+value if value.lstrip().startswith(('=', '+', '-', '@', '\t', '\r')) else value
    for c in result['candidates']:
        writer.writerow([safe_csv(result['election']['title']),safe_csv(c['full_name']),safe_csv(c['department']),c['votes'],c['percent']])
    return Response(output.getvalue(),mimetype='text/csv',headers={'Content-Disposition':f'attachment; filename="election-{election_id}-results.csv"'})
