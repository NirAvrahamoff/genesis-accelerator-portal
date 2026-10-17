# Original version (v1)

This folder keeps the first version of the portal, as I submitted it for the UX course, for comparison with the current version in the repository root.

It contains the original Flask app, templates, community-portal script and styles, the original README, and screenshots of the public pages. A few things were left out on purpose: the SQLite database (it held test submissions with real contact details), the investor contact list, photos of real mentors, and files unrelated to the project. A partner referral link was replaced with the partner's public site. The code is otherwise unchanged, so it will not run as-is without those files.

The live demo links in `README_original.md` now open the current version.

## What changed in the current version

| Area | v1 | Current |
|---|---|---|
| Admin dashboard | Open to anyone who knew the URL | Password-protected; contact details masked in demo mode |
| Security | No CSRF protection; applicant text inserted as HTML in the details view (XSS) | CSRF tokens; all user text inserted as text |
| Validation | Browser only | Server-side, with inline error messages |
| Community portal | Not connected to the app, and the script had a syntax error | Served by the app, with working filters and introduction requests stored in the database |
| Data | Real test submissions and a real investor list committed to the repo | Fictional demo data generated on first run |
| Fit Score | Inside `app.py`, undocumented | Separate module with documented weights and tests |
| Tests | None | 8 automated tests |
| Structure | App nested under `HTML/` alongside course exercises | One clean Flask project |
