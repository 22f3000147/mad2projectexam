
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

Start Redis, then run these in separate terminals from the `backend` folder:
```bash
redis-server                                        
python app.py                                       
celery -A celery_app.celery worker --loglevel=info  
celery -A celery_app.celery beat --loglevel=info    
```
| Job | When | What |
|---|---|---|
| Daily reminder | every day at `REMINDER_HOUR:REMINDER_MINUTE` (default 08:00) | mails students whose exam is today/tomorrow (exam, date/time, examiner, instructions). Also posts to Google Chat if `GCHAT_WEBHOOK_URL` is set |
| Monthly report | 1st of every month, 07:00 | HTML report (exams conducted, participants, examiners, pending evaluations, most active examiners) mailed to admin and saved in `backend/reports/` |
| CSV export | student clicks **Export history (CSV)** | async job, student gets an alert + mail when the file is ready |

Admin can also run the report/reminders on demand from the **Reports** page. Times use `TIMEZONE` (default Asia/Kolkata).
If Redis or the worker is not running the API answers `503` instead of hanging.

Redis db 2 caches the slow, frequently read API data (the app still works without Redis, just slower):

| Cached | Used by | Expires | Refreshed when these tables change |
|---|---|---|---|
| open exams list | student Exams / Home | 60 s | courses, exams, slots, bookings |
| exam schedule (slots) | student Slots / Home | 60 s | courses, exams, slots, bookings, users |
| rubrics of an exam | admin, examiner, student exam details | 10 min | rubrics |
| dashboard counts | admin Home | 60 s | users, courses, exams, slots, bookings |

* Only data that is the same for everybody is cached. Things that depend on the logged-in student
  ("already booked", "can book", cancel button) are added on top for each request, so students never see each other's data.
* Automatic refresh: a SQLAlchemy hook (`utils/cache.py`) clears the groups that depend on a table as soon as a commit changes it.
  Expiry (TTL) is the safety net. Admin can also press **Clear cache** on the Reports page.
* Every API response has an `X-Cache: HIT/MISS` header (Network tab).
* Measure it: `python benchmark_cache.py` (about 4-8x faster on the list endpoints).
* After deleting `emp.db` you do not need to flush Redis: cache keys are tagged with the database name.

Examiner login details are mailed when admin approves them. Set these env vars to use real SMTP,
otherwise the mail is printed in the terminal and the temp password is shown to the admin in the UI:
`MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, MAIL_FROM`

