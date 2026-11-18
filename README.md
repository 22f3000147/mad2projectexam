
Web app where **Admin**, **Examiner** and **Student** roles manage examinations, slots, bookings and evaluations.

- Flask (API) · VueJS via CDN (UI) · Jinja2 only for the single entry-point template
- Bootstrap (styling) · SQLite · Redis (cache) · Redis + Celery (batch jobs)

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py          # http://localhost:5000
```
Default admin (created programmatically on first run): `admin@emp.com` / `Admin@123`

Examiner login details are mailed when admin approves them. Set these env vars to use real SMTP,
otherwise the mail is printed in the terminal and the temp password is shown to the admin in the UI:
`MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, MAIL_FROM`

- [x] 0 – GitHub setup
- [x] 1 – Database models & schema
- [x] 2 – Authentication & RBAC
- [x] 3 – Admin dashboard & examination management
- [x] 4 – Examiner dashboard & slot management
- [x] 5 – Student dashboard & slot booking
- [x] 6 – Booking history & evaluation tracking
- [ ] 7 – Celery jobs (reminders, monthly report, CSV export)
- [ ] 8 – Redis caching
- [ ] 9 – (opt) UI/UX & PWA
- [ ] 10 – (opt) Charts & analytics

_(add problems + fixes here)_
