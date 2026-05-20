from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'helpdesk-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///helpdesk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'


# ── Models ────────────────────────────────────────────────────────────────────

class User(UserMixin, db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(80), unique=True, nullable=False)
    full_name    = db.Column(db.String(120), nullable=False)
    email        = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role         = db.Column(db.String(20), default='user')  # admin | staff | user

    tickets_created  = db.relationship('Ticket', foreign_keys='Ticket.created_by_id',  backref='creator',  lazy=True)
    tickets_assigned = db.relationship('Ticket', foreign_keys='Ticket.assigned_to_id', backref='assignee', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def initials(self):
        parts = self.full_name.split()
        return (parts[0][0] + parts[-1][0]).upper() if len(parts) > 1 else parts[0][0].upper()


class Ticket(db.Model):
    id             = db.Column(db.Integer, primary_key=True)
    title          = db.Column(db.String(200), nullable=False)
    description    = db.Column(db.Text, nullable=False)
    priority       = db.Column(db.String(20), nullable=False, default='medium')   # low | medium | high | critical
    category       = db.Column(db.String(30), nullable=False, default='software') # hardware | software | network
    status         = db.Column(db.String(20), nullable=False, default='open')     # open | in_progress | resolved | closed
    created_by_id  = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at     = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolution_notes = db.Column(db.Text, nullable=True)

    _PRIORITY_COLORS = {'low': 'badge-low', 'medium': 'badge-medium', 'high': 'badge-high', 'critical': 'badge-critical'}
    _STATUS_COLORS   = {'open': 'badge-open', 'in_progress': 'badge-in_progress', 'resolved': 'badge-resolved', 'closed': 'badge-closed'}
    _CATEGORY_ICONS  = {'hardware': 'bi-cpu', 'software': 'bi-code-square', 'network': 'bi-wifi'}

    @property
    def priority_class(self):
        return self._PRIORITY_COLORS.get(self.priority, 'badge-medium')

    @property
    def status_class(self):
        return self._STATUS_COLORS.get(self.status, 'badge-open')

    @property
    def status_display(self):
        return self.status.replace('_', ' ').title()

    @property
    def category_icon(self):
        return self._CATEGORY_ICONS.get(self.category, 'bi-question-circle')

    @property
    def ticket_number(self):
        return f'#{self.id:04d}'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ── Seed data ─────────────────────────────────────────────────────────────────

def seed_db():
    db.create_all()
    if User.query.first():
        return

    raw_users = [
        ('admin',       'Admin User',   'admin@helpdesk.com',       'admin123', 'admin'),
        ('john.smith',  'John Smith',   'john.smith@helpdesk.com',  'staff123', 'staff'),
        ('sarah.jones', 'Sarah Jones',  'sarah.jones@helpdesk.com', 'staff123', 'staff'),
        ('alice.brown', 'Alice Brown',  'alice@company.com',        'user123',  'user'),
        ('bob.davis',   'Bob Davis',    'bob@company.com',          'user123',  'user'),
    ]
    users = []
    for username, full_name, email, pw, role in raw_users:
        u = User(username=username, full_name=full_name, email=email, role=role)
        u.set_password(pw)
        db.session.add(u)
        users.append(u)
    db.session.flush()

    samples = [
        ('Laptop won\'t boot after Windows update',
         'My laptop shows a blue screen error (BSOD) after the latest Windows update was applied. Error code: 0x0000007E. Unable to work at all.',
         'critical', 'hardware', 'open',        3, None),
        ('Cannot connect to VPN from home',
         'Getting "Authentication failed" when connecting to the company VPN via Cisco AnyConnect. Issue started yesterday after password reset.',
         'high',     'network',  'in_progress',  3, 1),
        ('Outlook not syncing emails',
         'Emails are delayed by 2–3 hours for the entire Marketing team. Started Monday morning. Affects both sending and receiving.',
         'medium',   'software', 'in_progress',  4, 2),
        ('Request for additional monitor',
         'Need a second monitor to improve productivity on video editing tasks. Current single-screen setup is limiting efficiency.',
         'low',      'hardware', 'open',         4, None),
        ('Wi-Fi drops every 30 minutes on Floor 3',
         'Internet connection drops repeatedly on Floor 3. Must reconnect manually each time. Affects all ~20 users on that floor.',
         'high',     'network',  'open',         5, None),
        ('Adobe Photoshop license expired',
         'Cannot open Photoshop — license expired error shown. Need renewal for the design team (5 users). Blocking current project deadline.',
         'medium',   'software', 'resolved',     4, 2),
        ('Printer offline — Marketing dept',
         'HP LaserJet Pro on Floor 2 shows as offline. Tried power cycling and reinstalling drivers. No improvement.',
         'medium',   'hardware', 'closed',       5, 1),
        ('New employee laptop setup request',
         'New hire starting Monday needs a laptop configured with standard software suite: Office 365, Slack, Zoom, and VPN client.',
         'low',      'software', 'open',         3, None),
    ]

    for title, desc, priority, category, status, ci, ai in samples:
        t = Ticket(
            title=title, description=desc, priority=priority,
            category=category, status=status,
            created_by_id=users[ci - 1].id,
            assigned_to_id=users[ai - 1].id if ai else None,
        )
        if status in ('resolved', 'closed'):
            t.resolution_notes = 'Issue investigated and resolved. Confirmed working by the end user.'
        db.session.add(t)

    db.session.commit()


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=bool(request.form.get('remember')))
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(request.args.get('next') or url_for('dashboard'))
        flash('Invalid username or password. Please try again.', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/')
@login_required
def dashboard():
    stats = {
        'total':       Ticket.query.count(),
        'open':        Ticket.query.filter_by(status='open').count(),
        'in_progress': Ticket.query.filter_by(status='in_progress').count(),
        'resolved':    Ticket.query.filter_by(status='resolved').count(),
        'closed':      Ticket.query.filter_by(status='closed').count(),
        'critical':    Ticket.query.filter(
                           Ticket.priority == 'critical',
                           Ticket.status.notin_(['resolved', 'closed'])
                       ).count(),
    }
    recent = Ticket.query.order_by(Ticket.created_at.desc()).limit(8).all()
    return render_template('dashboard.html', stats=stats, recent=recent)


@app.route('/tickets')
@login_required
def tickets():
    status_f   = request.args.get('status', '')
    priority_f = request.args.get('priority', '')
    category_f = request.args.get('category', '')
    search     = request.args.get('search', '').strip()

    query = Ticket.query
    if current_user.role == 'user':
        query = query.filter_by(created_by_id=current_user.id)
    if status_f:
        query = query.filter_by(status=status_f)
    if priority_f:
        query = query.filter_by(priority=priority_f)
    if category_f:
        query = query.filter_by(category=category_f)
    if search:
        query = query.filter(db.or_(
            Ticket.title.ilike(f'%{search}%'),
            Ticket.description.ilike(f'%{search}%'),
        ))

    all_tickets = query.order_by(Ticket.created_at.desc()).all()
    return render_template('tickets.html', tickets=all_tickets,
        status_f=status_f, priority_f=priority_f, category_f=category_f, search=search)


@app.route('/tickets/new', methods=['GET', 'POST'])
@login_required
def create_ticket():
    if request.method == 'POST':
        ticket = Ticket(
            title=request.form['title'].strip(),
            description=request.form['description'].strip(),
            priority=request.form['priority'],
            category=request.form['category'],
            created_by_id=current_user.id,
        )
        db.session.add(ticket)
        db.session.commit()
        flash(f'Ticket {ticket.ticket_number} created successfully!', 'success')
        return redirect(url_for('ticket_detail', ticket_id=ticket.id))
    return render_template('create_ticket.html')


@app.route('/tickets/<int:ticket_id>')
@login_required
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if current_user.role == 'user' and ticket.created_by_id != current_user.id:
        flash('You do not have permission to view this ticket.', 'danger')
        return redirect(url_for('tickets'))
    staff = User.query.filter(User.role.in_(['admin', 'staff'])).all()
    return render_template('ticket_detail.html', ticket=ticket, staff=staff)


@app.route('/tickets/<int:ticket_id>/update', methods=['POST'])
@login_required
def update_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if current_user.role == 'user':
        flash('Permission denied.', 'danger')
        return redirect(url_for('ticket_detail', ticket_id=ticket_id))

    action = request.form.get('action')

    if action == 'assign':
        val = request.form.get('assigned_to_id')
        ticket.assigned_to_id = int(val) if val else None
        if ticket.status == 'open' and val:
            ticket.status = 'in_progress'
        flash('Ticket assigned successfully.', 'success')

    elif action == 'status':
        ticket.status = request.form.get('status', ticket.status)
        notes = request.form.get('resolution_notes', '').strip()
        if notes:
            ticket.resolution_notes = notes
        flash(f'Status updated to {ticket.status_display}.', 'success')

    elif action == 'resolve':
        ticket.status = 'resolved'
        ticket.resolution_notes = request.form.get('resolution_notes', '').strip()
        flash('Ticket resolved successfully.', 'success')

    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('ticket_detail', ticket_id=ticket_id))


if __name__ == '__main__':
    with app.app_context():
        seed_db()
    app.run(debug=True)
