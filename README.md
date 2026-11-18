
Web app where **Admin**, **Examiner** and **Student** roles manage examinations, slots, bookings and evaluations.

- Flask (API) · VueJS via CDN (UI) · Jinja2 only for the single entry-point template
- Bootstrap (styling) · SQLite · Redis (cache) · Redis + Celery (batch jobs)

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py         
```
Default admin (created programmatically on first run): `admin@emp.com` / `Admin@123`

Start Redis, then run these in separate terminals from the `backend` folder:
```bash
redis-server                                        
python app.py                                       
celery -A celery_app.celery worker --loglevel=info  jobs   (add --pool=solo on Windows)
celery -A celery_app.celery beat --loglevel=info    
```
| Job | When | What |
|---|---|---|
| Daily reminder | every day at `REMINDER_HOUR:REMINDER_MINUTE` (default 08:00) | mails students whose exam is today/tomorrow (exam, date/time, examiner, instructions). Also posts to Google Chat if `GCHAT_WEBHOOK_URL` is set |
| Monthly report | 1st of every month, 07:00 | HTML report (exams conducted, participants, examiners, pending evaluations, most active examiners) mailed to admin and saved in `backend/reports/` |
| CSV export | student clicks **Export history (CSV)** | async job, student gets an alert + mail when the file is ready |

Admin can also run the report/reminders on demand from the **Reports** page. Times use `TIMEZONE` (default Asia/Kolkata).
If Redis or the worker is not running the API answers `503` instead of hanging.

Examiner login details are mailed when admin approves them. Set these env vars to use real SMTP,
otherwise the mail is printed in the terminal and the temp password is shown to the admin in the UI:
`MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, MAIL_FROM`



