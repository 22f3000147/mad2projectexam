import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\d{10}$")


def validate_registration(d):
    errors = {}
    if not EMAIL_RE.match((d.get("email") or "").strip()):
        errors["email"] = "Valid email required"
    if len(d.get("password") or "") < 6:
        errors["password"] = "Password must be at least 6 characters"
    if not (d.get("full_name") or "").strip():
        errors["full_name"] = "Full name required"
    phone = (d.get("phone") or "").strip()
    if phone and not PHONE_RE.match(phone):
        errors["phone"] = "Phone must be 10 digits"
    return errors
