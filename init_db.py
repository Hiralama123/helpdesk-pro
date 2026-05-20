"""
Database initialisation script.

Run this once before starting the application to create all tables and
populate the database with seed data (demo users and sample tickets).

Usage:
    python init_db.py

On Railway this is executed automatically as the pre-deploy command so
the schema is always in place before gunicorn starts serving requests.
"""

from app import app, seed_db

with app.app_context():
    seed_db()
    print("Database initialised successfully.")
