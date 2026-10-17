import os
import sqlite3
from datetime import datetime, date
from zoneinfo import ZoneInfo
from flask import Flask, request, redirect, render_template

# =========================
# Flask app initialization
# יצירת אפליקציית Flask
# =========================
app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "genesis.db")


# =========================
# Database connection helper
# פותחת חיבור ל-SQLite ומחזירה rows כ-dictionary
# =========================
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    return conn


# =========================
# Database initialization
# יוצרת טבלת applications עם כל שדות הטופס אם אינה קיימת
# רצה פעם אחת עם עליית השרת
# =========================
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submitted_at TEXT,

            full_name TEXT,
            email TEXT,
            linkedin TEXT,
            phone TEXT,

            role_in_company TEXT,
            company_name TEXT,

            gain_from_program TEXT,
            primary_sector TEXT,
            startup_stage TEXT,

            cofounders_count INTEGER,
            time_working_on_startup TEXT,
            cofounders_details TEXT,

            company_founded_date TEXT,
            startup_description TEXT,
            team_unique TEXT,
            current_customers TEXT,
            goals_next_6_months TEXT,

            raised_funding TEXT,
            funding_from_whom TEXT,
            revenue_past_year TEXT,

            website_link TEXT,
            participated_accelerator TEXT,
            heard_about_us TEXT,
            additional_info TEXT
        )
    """)

    conn.commit()
    conn.close()


# אתחול בסיס הנתונים
init_db()


# =========================
# Route: Landing Page
# מציג את דף הנחיתה הראשי
# =========================
@app.route("/")
def landing():
    return render_template("Landing_page.html")


# =========================
# Route: Application Form
# מציג את טופס ההרשמה המלא
# =========================
@app.route("/apply")
def apply():
    return render_template(
        "Registration_form.html",
        today=date.today().isoformat()
    )


# =========================
# Route: Approval Page
# מוצג לאחר שליחת טופס מוצלחת
# =========================
@app.route("/approval")
def approval():
    return render_template("approval.html")


# =========================
# Route: Form Submission
# מקבל נתוני POST מהטופס
# שומר את כל השדות בבסיס הנתונים
# שומר שעה ישראלית בפורמט קריא
# =========================
@app.route("/submit", methods=["POST"])
def submit():
    data = request.form

    # איסוף ערכי checkbox של gain
    gain_values = request.form.getlist("gain[]")
    gain_joined = ", ".join(gain_values)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO applications (
            submitted_at,
            full_name, email, linkedin, phone,
            role_in_company, company_name,
            gain_from_program,
            primary_sector, startup_stage,
            cofounders_count, time_working_on_startup,
            cofounders_details,
            company_founded_date,
            startup_description, team_unique,
            current_customers, goals_next_6_months,
            raised_funding, funding_from_whom,
            revenue_past_year,
            website_link,
            participated_accelerator,
            heard_about_us,
            additional_info
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        # שעה ישראלית
        datetime.now(ZoneInfo("Asia/Jerusalem")).strftime("%Y-%m-%d %H:%M:%S"),

        data.get("full_name"),
        data.get("email"),
        data.get("linkedin"),
        data.get("phone"),

        data.get("role_in_company"),
        data.get("company_name"),

        gain_joined,
        data.get("primary_sector"),
        data.get("startup_stage"),

        data.get("cofounders_count"),
        data.get("time_working_on_startup"),
        data.get("cofounders_details"),

        data.get("company_founded_date"),
        data.get("startup_description"),
        data.get("team_unique"),
        data.get("current_customers"),
        data.get("goals_next_6_months"),

        data.get("raised_funding"),
        data.get("funding_from_whom"),
        data.get("revenue_past_year"),

        data.get("website_link"),
        data.get("participated_accelerator"),
        data.get("heard_about_us"),
        data.get("additional_info")
    ))

    conn.commit()
    conn.close()

    return redirect("/approval")

@app.route("/admin")
def admin():
    sort_by = request.args.get("sort", "date")
    min_score = request.args.get("min_score")

    conn = get_db_connection()
    raw_rows = conn.execute("SELECT * FROM applications").fetchall()
    conn.close()

    rows = []
    for r in raw_rows:
        row_dict = dict(r)
        row_dict["fit_score"] = calculate_fit_score(row_dict)
        rows.append(row_dict)

    # סינון לפי דירוג מינימלי
    if min_score and min_score.isdigit():
        min_score = int(min_score)
        rows = [r for r in rows if r["fit_score"] >= min_score]

    # מיון
    if sort_by == "fit":
        rows.sort(key=lambda x: x["fit_score"], reverse=True)
    else:
        rows.sort(key=lambda x: x["submitted_at"], reverse=True)

    return render_template(
        "admin.html",
        rows=rows,
        total_count=len(raw_rows),
        filtered_count=len(rows),
        min_score=min_score
    )


def calculate_fit_score(data):
    score = 0

    # =========================
    # 1. Startup stage (max 2)
    # =========================
    stage = data.get("startup_stage")
    if stage in ["Pre-Seed", "Seed"]:
        score += 2
    elif stage == "Early revenue":
        score += 1


    # =========================
    # 2. Co-founders count (max 2)
    # =========================
    founders_raw = data.get("cofounders_count", "0")

    try:
        founders = int(founders_raw)
    except (ValueError, TypeError):
        founders = 0

    if founders >= 2:
        score += 2
    elif founders == 1:
        score += 1

    # =========================
    # 3. Time working on startup (max 4) ⭐
    # =========================
    time_active = data.get("time_working_on_startup")

    if time_active == "lt_3":
        score += 0
    elif time_active == "3_6":
        score += 2
    elif time_active == "6_24":
        score += 4
    elif time_active == "gt_24":
        score += 2


    # =========================
    # 4. Customers exist (max 1)
    # =========================
    if data.get("current_customers"):
        score += 1


    # =========================
    # 5. Funding raised (max 1)
    # =========================
    if data.get("raised_funding") == "Yes":
        score += 1

    return score



# =========================
# Run Flask development server
# =========================
if __name__ == "__main__":
    app.run(debug=True)


