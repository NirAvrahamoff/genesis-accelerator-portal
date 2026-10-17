"""Startup accelerator portal: public site, application form, community portal and admin dashboard."""
import csv
import hmac
import io
import json
import os
import secrets
from collections import Counter
from datetime import date
from functools import wraps
from pathlib import Path

from flask import (Flask, Response, abort, flash, redirect, render_template, request,
                   session, url_for)

import db
import forms
from scoring import MAX_SCORE, fit_score, score_band

BASE = Path(__file__).parent


def env_flag(name, default):
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes")


def create_app(test_config=None):
    app = Flask(__name__)
    demo = env_flag("DEMO_MODE", "1")
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        DATABASE=os.environ.get("DATABASE", str(BASE / "instance" / "portal.db")),
        DEMO_MODE=demo,
        # In demo mode the admin password defaults to "demo" so reviewers can see the dashboard.
        ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD") or ("demo" if demo else None),
        SHOW_DEMO_PASSWORD=demo and not os.environ.get("ADMIN_PASSWORD"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config:
        app.config.update(test_config)

    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    db.init(app.config["DATABASE"], seed_demo=app.config["DEMO_MODE"])
    community = json.loads((BASE / "data" / "community.json").read_text())

    # ------------------------------------------------------------ helpers
    def conn():
        return db.connect(app.config["DATABASE"])

    def csrf_token():
        if "csrf" not in session:
            session["csrf"] = secrets.token_hex(16)
        return session["csrf"]

    def check_csrf():
        sent = request.form.get("csrf") or request.headers.get("X-CSRF-Token", "")
        expected = session.get("csrf", "")
        if not expected or not hmac.compare_digest(sent, expected):
            abort(400, "Invalid form token. Please reload the page and try again.")

    def admin_required(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if not session.get("admin"):
                return redirect(url_for("login", next=request.path))
            return view(*args, **kwargs)
        return wrapper

    def mask_email(value):
        name, _, domain = (value or "").partition("@")
        return f"{name[:1]}***@{domain}" if domain else ""

    def present(row):
        """Prepare a row for the dashboard. In demo mode, contact details of real submissions are hidden."""
        r = dict(row)
        r["fit_score"] = fit_score(r)
        r["band"] = score_band(r["fit_score"])
        r["time_label"] = forms.TIME_WORKING.get(r["time_working_on_startup"], "")
        r["revenue_label"] = forms.REVENUE.get(r["revenue_past_year"], "")
        r["cofounders_label"] = forms.COFOUNDERS.get(r["cofounders_count"], "")
        if app.config["DEMO_MODE"] and r["is_demo"] != "1":
            r["email"], r["phone"], r["linkedin"] = mask_email(r["email"]), "hidden in demo", ""
        return r

    app.add_template_filter(lambda xs: [(x, x) for x in xs], "zip_self")

    @app.context_processor
    def inject():
        return {"csrf_token": csrf_token, "demo_mode": app.config["DEMO_MODE"], "forms": forms}

    # ------------------------------------------------------------ public pages
    @app.get("/")
    def landing():
        return render_template("landing.html")

    @app.get("/apply")
    def apply():
        return render_template("apply.html", values={}, errors={}, today=date.today().isoformat())

    @app.post("/apply")
    def submit():
        check_csrf()
        data, errors = forms.validate(request.form)
        if errors:
            values = {**data, "gain": request.form.getlist("gain"), "consent": request.form.get("consent") == "on"}
            return render_template("apply.html", values=values, errors=errors,
                                   today=date.today().isoformat()), 400
        with conn() as c:
            db.insert_application(c, data)
        return redirect(url_for("submitted"))

    @app.get("/submitted")
    def submitted():
        return render_template("submitted.html")

    @app.get("/community")
    def community_portal():
        sectors = sorted({s for inv in community["investors"] for s in inv["sectors"]})
        return render_template("community.html", data=community, investor_sectors=sectors)

    @app.post("/community/intro")
    def intro_request():
        check_csrf()
        target_type = request.form.get("target_type", "")
        target_name = request.form.get("target_name", "").strip()[:120]
        email = request.form.get("email", "").strip()[:200]
        message = request.form.get("message", "").strip()[:2000]
        valid_names = {x["name"] for k in ("startups", "mentors", "investors") for x in community[k]}
        if target_type not in ("startup", "mentor", "investor") or target_name not in valid_names \
                or not forms.EMAIL_RE.match(email) or not message:
            return {"ok": False, "error": "Please enter a valid email and a message."}, 400
        with conn() as c:
            db.insert_intro_request(c, target_type, target_name, email, message)
        return {"ok": True}

    # ------------------------------------------------------------ admin
    @app.route("/admin/login", methods=["GET", "POST"])
    def login():
        if app.config["ADMIN_PASSWORD"] is None:
            abort(503, "The admin dashboard is disabled. Set ADMIN_PASSWORD to enable it.")
        if request.method == "POST":
            check_csrf()
            if hmac.compare_digest(request.form.get("password", ""), app.config["ADMIN_PASSWORD"]):
                session.clear()
                session["admin"] = True
                nxt = request.args.get("next", "")
                return redirect(nxt if nxt.startswith("/admin") else url_for("admin"))
            flash("Wrong password.")
        return render_template("login.html")

    @app.post("/admin/logout")
    def logout():
        check_csrf()
        session.clear()
        return redirect(url_for("landing"))

    @app.get("/admin")
    @admin_required
    def admin():
        with conn() as c:
            rows = [present(r) for r in c.execute("SELECT * FROM applications ORDER BY submitted_at DESC")]
            intros = [dict(r) for r in c.execute("SELECT * FROM intro_requests ORDER BY submitted_at DESC")]
        if app.config["DEMO_MODE"]:
            for r in intros:
                r["requester_email"] = mask_email(r["requester_email"])
        summary = {
            "total": len(rows),
            "high_fit": sum(r["band"] == "high" for r in rows),
            "funded": sum(r["raised_funding"] == "Yes" for r in rows),
            "intros": len(intros),
        }
        charts = {
            "sector": Counter(r["primary_sector"] or "Not set" for r in rows).most_common(),
            "stage": [(s, sum(r["startup_stage"] == s for r in rows)) for s in forms.STAGES],
            "score": [(str(s), sum(r["fit_score"] == s for r in rows)) for s in range(MAX_SCORE + 1)],
        }
        return render_template("admin.html", rows=rows, intros=intros, summary=summary,
                               charts=charts, max_score=MAX_SCORE)

    @app.get("/admin/export.csv")
    @admin_required
    def export_csv():
        with conn() as c:
            rows = [present(r) for r in c.execute("SELECT * FROM applications ORDER BY submitted_at DESC")]
        cols = ["id", "submitted_at", "full_name", "email", "phone", "linkedin", "company_name", "role_in_company",
                "primary_sector", "startup_stage", "cofounders_label", "time_label", "raised_funding",
                "revenue_label", "fit_score"]
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        return Response(buf.getvalue(), mimetype="text/csv",
                        headers={"Content-Disposition": "attachment; filename=applications.csv"})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=env_flag("FLASK_DEBUG", "0"))
