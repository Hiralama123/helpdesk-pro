import sys
sys.path.insert(0, '.')

from app import app, db

def seed_db():
    from app import User, Ticket
    
    if User.query.count() == 0:
        from werkzeug.security import generate_password_hash
        users = [
            User(username='admin', full_name='Admin User', 
                 email='admin@helpdesk.com', role='admin',
                 password_hash=generate_password_hash('admin123')),
            User(username='john.smith', full_name='John Smith',
                 email='john@helpdesk.com', role='staff',
                 password_hash=generate_password_hash('staff123')),
            User(username='alice.brown', full_name='Alice Brown',
                 email='alice@helpdesk.com', role='user',
                 password_hash=generate_password_hash('user123')),
        ]
        db.session.add_all(users)
        db.session.commit()
        print("Users created!")

with app.app_context():
    db.create_all()
    seed_db()
    print("Database ready!")