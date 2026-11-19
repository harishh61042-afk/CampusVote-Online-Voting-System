"""CampusVote app factory."""
from datetime import timedelta
from functools import wraps
from pathlib import Path
import os
import secrets
import hmac
from flask import (Flask, abort, g, redirect, render_template, request, session,
                   url_for, flash)
from campusvote.db import get_db, close_db, init_schema, election_state


def create_app(test_config=None):
    root = Path(__file__).resolve().parent.parent
    instance = root / 'instance'
    instance.mkdir(exist_ok=True)
    secret_file = instance / '.secret_key'
    if not secret_file.exists() and not (test_config and 'SECRET_KEY' in test_config):
        secret_file.write_text(secrets.token_hex(32), encoding='utf-8')
        try: os.chmod(secret_file, 0o600)
        except OSError: pass
    secret = os.getenv('CAMPUSVOTE_SECRET') or (secret_file.read_text().strip() if secret_file.exists() else secrets.token_hex(32))
    app = Flask(__name__, instance_path=str(instance))
    app.config.update(SECRET_KEY=secret, DATABASE=os.getenv('CAMPUSVOTE_DB', str(instance/'campusvote.sqlite3')),
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
                      SESSION_COOKIE_SECURE=os.getenv('CAMPUSVOTE_HTTPS') == '1',
                      PERMANENT_SESSION_LIFETIME=timedelta(hours=4), MAX_CONTENT_LENGTH=1024*1024)
    if test_config: app.config.update(test_config)
    init_schema(app.config['DATABASE'])
    app.teardown_appcontext(close_db)

    @app.before_request
    def load_user_and_csrf():
        g.user = None
        if 'user_id' in session:
            g.user = get_db().execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
            if g.user is None:
                session.clear()
        if '_csrf' not in session:
            session['_csrf'] = secrets.token_urlsafe(32)
        if request.method in ('POST','PUT','PATCH','DELETE'):
            token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token') or ''
            if not hmac.compare_digest(session['_csrf'], token):
                abort(400, description='The form expired or could not be verified. Refresh and try again.')

    @app.after_request
    def security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'self'; form-action 'self'"
        return response

    @app.context_processor
    def globals_for_templates():
        return {'csrf_token': lambda: session.get('_csrf',''), 'current_user': g.get('user'),
                'election_state': election_state}

    @app.template_filter('ist')
    def format_ist(value):
        from datetime import datetime, timezone, timedelta
        if not value: return '—'
        try:
            d = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
            return d.astimezone(timezone(timedelta(hours=5, minutes=30))).strftime('%d %b %Y, %I:%M %p IST')
        except (ValueError, TypeError):
            return value

    @app.template_filter('ist_input')
    def format_ist_input(value):
        from datetime import datetime, timezone, timedelta
        if not value: return ''
        d = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
        return d.astimezone(timezone(timedelta(hours=5, minutes=30))).strftime('%Y-%m-%dT%H:%M')

    from campusvote.auth.routes import bp as auth_bp
    from campusvote.admin.routes import bp as admin_bp
    from campusvote.voting.routes import bp as voting_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(voting_bp)

    @app.get('/')
    def home():
        if g.user:
            return redirect(url_for('admin.dashboard' if g.user['role']=='admin' else 'voting.dashboard'))
        return render_template('home.html', page='home')

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(500)
    def error_page(e):
        code = getattr(e,'code',500)
        return render_template('errors/error.html', code=code, message=getattr(e,'description','Something went wrong.')), code

    import click
    from werkzeug.security import generate_password_hash
    from campusvote.db import now_utc
    @app.cli.command('create-admin')
    @click.option('--id', 'admin_id', prompt='Admin ID')
    @click.option('--name', prompt='Full name')
    @click.password_option(confirmation_prompt=True)
    def create_admin(admin_id, name, password):
        """Create the first administrator (password entered securely)."""
        if len(password) < 10: raise click.ClickException('Password must have at least 10 characters.')
        con = get_db()
        try:
            con.execute('INSERT INTO users(student_id,full_name,password_hash,role,approval_status,created_at) VALUES(?,?,?,?,?,?)',
                        (admin_id.strip(),name.strip(),generate_password_hash(password),'admin','approved',now_utc()))
        except Exception as exc:
            raise click.ClickException('Admin could not be created; check for a duplicate ID.') from exc
        click.echo('Administrator created. You can log in.')
    return app


def login_required(view):
    @wraps(view)
    def inner(*args, **kwargs):
        if not g.user:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('auth.login'))
        return view(*args, **kwargs)
    return inner


def role_required(role):
    def decorator(view):
        @wraps(view)
        @login_required
        def inner(*args, **kwargs):
            if g.user['role'] != role:
                abort(403)
            return view(*args, **kwargs)
        return inner
    return decorator
