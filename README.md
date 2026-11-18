
Web app where **Admin**, **Examiner** and **Student** roles can manage examinations, slots, bookings and evaluations.

- Flask (API) · VueJS via CDN (UI) · Jinja2 only for the single entry-point template
- Bootstrap (styling) · SQLite · Redis (cache) · Redis + Celery (batch jobs)

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py         
```
Default admin (created programmatically on first run): `admin@emp.com` / `Admin@123`

Examiner login details are mailed when admin approves them. Set these env vars to use real SMTP,
otherwise the mail is printed in the terminal and the temp password is shown to the admin in the UI:
`MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, MAIL_FROM`

