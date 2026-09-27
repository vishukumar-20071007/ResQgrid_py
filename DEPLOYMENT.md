# ResQGrid Deployment Guide

## GitHub → Render

1. Create a GitHub repository named `resqgrid`.
2. Upload all files from this folder to the repository.
3. On Render, choose **New → Web Service** and connect the GitHub repo.
4. Build command: `pip install -r requirements.txt`
5. Start command: `gunicorn app:app`
6. Click Deploy. Render will provide a public URL.

## Local test

Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Database

This version uses SQLite for the college/demo prototype. For a serious public deployment, migrate to PostgreSQL because cloud filesystem storage should not be treated as permanent application data.

## Future production upgrades

- PostgreSQL
- Authentication and role-based access
- HTTPS and secure secrets
- Input validation and audit logs
- Real routing/traffic ETA
- WebSockets for live updates
- Backups, monitoring and privacy/security review

**Safety:** This is an educational prototype, not a real emergency-dispatch or medical decision system.
