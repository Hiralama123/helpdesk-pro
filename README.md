# HelpDesk Pro 🎫

A full-featured IT Help Desk ticketing system built with Flask.

## Live Demo
🌐 https://helpdesk-pro-production-b514.up.railway.app

## Demo Login
| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Staff | john.smith | staff123 |
| User | alice.brown | user123 |

## Features
- Role-based login (Admin, Staff, User)
- Dashboard with ticket statistics
- Create tickets with priority and category
- Assign tickets to staff members
- Status workflow: Open → In Progress → Resolved → Closed
- Search and filter tickets
- Resolution notes

## Tech Stack
- Python, Flask, Flask-SQLAlchemy
- Flask-Login for authentication
- SQLite database
- Deployed on Railway

## Run Locally
```bash
pip install -r requirements.txt
python app.py
```
