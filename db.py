"""SQLite storage for applications and introduction requests."""
import random
import sqlite3
from datetime import datetime, timedelta

from forms import CHOICE_FIELDS, GAINS, TEXT_FIELDS

APP_COLUMNS = ["submitted_at"] + TEXT_FIELDS + list(CHOICE_FIELDS) + ["gain_from_program", "is_demo"]

SCHEMA = f"""
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    {", ".join(f"{c} TEXT" for c in APP_COLUMNS)}
);
CREATE TABLE IF NOT EXISTS intro_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submitted_at TEXT,
    target_type TEXT,
    target_name TEXT,
    requester_email TEXT,
    message TEXT
);
"""


def connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init(path, seed_demo=True):
    with connect(path) as conn:
        conn.executescript(SCHEMA)
        empty = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0] == 0
        if seed_demo and empty:
            for app in demo_applications():
                insert_application(conn, app, is_demo=True)


def insert_application(conn, data, is_demo=False):
    row = {c: data.get(c, "") for c in APP_COLUMNS}
    row["submitted_at"] = data.get("submitted_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row["is_demo"] = "1" if is_demo else "0"
    conn.execute(
        f"INSERT INTO applications ({', '.join(APP_COLUMNS)}) VALUES ({', '.join('?' * len(APP_COLUMNS))})",
        [row[c] for c in APP_COLUMNS],
    )


def insert_intro_request(conn, target_type, target_name, email, message):
    conn.execute(
        "INSERT INTO intro_requests (submitted_at, target_type, target_name, requester_email, message) VALUES (?, ?, ?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), target_type, target_name, email, message),
    )


# ---------------------------------------------------------------- synthetic demo data
FIRST = ["Noa", "Itai", "Maya", "Omer", "Yael", "Daniel", "Tamar", "Eitan", "Shira", "Lior", "Adi", "Roni",
         "Gal", "Dana", "Yonatan", "Michal", "Amit", "Neta", "Ido", "Hila"]
LAST = ["Levin", "Barak", "Shalev", "Navon", "Peretz", "Golan", "Harel", "Segal", "Adler", "Mor", "Katz", "Oren"]
PREFIX = ["Nova", "Flux", "Orbit", "Pulse", "Quanta", "Vertex", "Lumen", "Apex", "Kite", "Helix", "Mosaic", "Tidal"]
SUFFIX = ["AI", "Labs", "Health", "Pay", "Shield", "Data", "Cloud", "Robotics", "Grid", "Ops"]
ROLES = ["CEO", "CTO", "COO", "Co-founder", "CPO"]


def demo_applications(n=48, seed=7):
    rng = random.Random(seed)
    start = datetime(2026, 1, 5, 9, 0)
    apps = []
    for i in range(n):
        first, last = rng.choice(FIRST), rng.choice(LAST)
        company = f"{rng.choice(PREFIX)}{rng.choice(SUFFIX)}"
        stage = rng.choices(["Ideation", "Pre-Seed", "Seed", "Early revenue"], [2, 5, 4, 2])[0]
        has_customers = stage in ("Seed", "Early revenue") or rng.random() < 0.3
        apps.append({
            "submitted_at": (start + timedelta(days=rng.randint(0, 80), minutes=rng.randint(0, 600))).strftime("%Y-%m-%d %H:%M:%S"),
            "full_name": f"{first} {last}",
            "email": f"{first.lower()}@{company.lower()}.example",
            "linkedin": f"https://www.linkedin.com/in/demo-{first.lower()}-{last.lower()}-{i}",
            "phone": f"050-000-{1000 + i}",
            "role_in_company": rng.choice(ROLES),
            "company_name": company,
            "primary_sector": rng.choice(CHOICE_FIELDS["primary_sector"][:-1]),
            "startup_stage": stage,
            "cofounders_count": rng.choices(["1", "2", "3"], [3, 5, 2])[0],
            "time_working_on_startup": rng.choices(["lt_3", "3_6", "6_24", "gt_24"], [2, 3, 5, 2])[0],
            "raised_funding": rng.choices(["Yes", "No"], [2, 3])[0],
            "revenue_past_year": "none" if not has_customers else rng.choice(["lt_50k", "50_250k", "250k_1m"]),
            "current_customers": "Two paying pilots with mid-size companies" if has_customers else "",
            "startup_description": f"{company} is a fictional demo startup in the {stage} stage.",
            "goals_next_6_months": "Close first U.S. design partners and prepare a seed round.",
            "gain_from_program": ", ".join(rng.sample(list(GAINS)[:-1], rng.randint(1, 3))),
        })
    return apps
