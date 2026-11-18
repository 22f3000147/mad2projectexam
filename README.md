# Examination Management Portal (EMP) V2 — MAD-II

Web app where **Admin**, **Examiner** and **Student** roles can manage examinations, slots, bookings and evaluations according to their functionality .

## Stack
- Flask (API) · VueJS via CDN (UI) · Jinja2 only for the single entry-point template
- Bootstrap (styling) · SQLite · Redis (cache) · Redis + Celery (batch jobs)

## Run locally
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py          # http://localhost:5000
```
Default admin (created on first run): `admin@emp.com` / `Admin@123`


