"""Public auth and student profile."""
import re
import sqlite3
from flask import Blueprint, request, render_template, redirect, url_for, flash, g, session
from werkzeug.security import generate_password_hash, check_password_hash
from campusvote import login_required
from campusvote.db import get_db, now_utc

bp = Blueprint('auth', __name__)


def valid_password(p):
    return len(p) >= 10 and any(c.isalpha() for c in p) and any(c.isdigit() for c in p)


@bp.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('full_name','').strip()
        student_id = request.form.get('student_id','').strip().upper()
        email = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        error = None
        if not (2 <= len(name) <= 100): error = 'Enter your full name (2–100 characters).'
        elif not re.fullmatch(r'[A-Z0-9_-]{3,25}', student_id): error = 'Student ID must contain 3–25 letters, numbers, - or _.'
        elif email and (len(email)>254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email)):
            error='Enter a valid email address.'
        elif not valid_password(password): error='Use at least 10 characters with a letter and a number.'
        elif password != request.form.get('confirm_password'): error='Passwords do not match.'
        elif request.form.get('terms') != 'yes': error='Please accept the election rules.'
        if error:
            flash(error,'error')
        else:
            try:
                get_db().execute('''INSERT INTO users(student_id,full_name,email,password_hash,role,approval_status,created_at)
                    VALUES(?,?,?,?,?,?,?)''', (student_id,name,email or None,generate_password_hash(password),'student','pending',now_utc()))
            except sqlite3.IntegrityError:
                flash('This student ID is already registered.','error')
            else:
                flash('Account created! An administrator must approve it before you can vote.','success')
                return redirect(url_for('auth.login'))
    return render_template('auth/register.html', page='register')


@bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('student_id','').strip().upper()
        password = request.form.get('password','')
        user = get_db().execute('SELECT * FROM users WHERE student_id=?', (identifier,)).fetchone()
        if not user or not check_password_hash(user['password_hash'], password):
            flash('Invalid ID or password.','error')
        elif user['approval_status'] == 'rejected':
            flash('This account was rejected. Contact the election administrator.','error')
        else:
            session.clear()
            session['user_id'] = user['id']
            session.permanent = True
            return redirect(url_for('admin.dashboard' if user['role']=='admin' else 'voting.dashboard'))
    return render_template('auth/login.html', page='login')


@bp.post('/logout')
@login_required
def logout():
    session.clear()
    flash('You have been signed out.','success')
    return redirect(url_for('auth.login'))


@bp.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    if request.method == 'POST':
        old = request.form.get('old_password','')
        new = request.form.get('new_password','')
        if not check_password_hash(g.user['password_hash'],old):
            flash('Your current password is incorrect.','error')
        elif not valid_password(new):
            flash('New password must be at least 10 characters and contain letters and numbers.','error')
        elif new != request.form.get('confirm_password'):
            flash('New passwords do not match.','error')
        else:
            get_db().execute('UPDATE users SET password_hash=? WHERE id=?',(generate_password_hash(new),g.user['id']))
            flash('Password updated.','success')
            return redirect(url_for('auth.profile'))
    return render_template('auth/profile.html', page='profile')
