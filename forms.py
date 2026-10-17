"""Application form definition and server-side validation."""
import re

SECTORS = ["AI", "FinTech", "Cyber", "HealthTech", "SaaS", "Cloud", "Robotics", "Data", "Climate", "Other"]
STAGES = ["Ideation", "Pre-Seed", "Seed", "Early revenue"]
GAINS = {
    "Mentoring": "Mentoring",
    "Customers": "Access to customers or design partners",
    "Investors": "Access to investors and fundraising support",
    "Education": "Educational content on company-building",
    "Networking": "Networking with fellow founders",
    "Tech": "Technical support",
    "Other": "Other",
}
COFOUNDERS = {"1": "1", "2": "2", "3": "More than 2"}
TIME_WORKING = {"lt_3": "Less than 3 months", "3_6": "3-6 months", "6_24": "6 months - 2 years", "gt_24": "More than 2 years"}
REVENUE = {"none": "No revenue yet", "lt_50k": "Less than $50k", "50_250k": "$50k-$250k", "250k_1m": "$250k-$1M", "gt_1m": "$1M+"}
YES_NO = ["Yes", "No"]

TEXT_FIELDS = [
    "full_name", "email", "linkedin", "phone", "role_in_company", "company_name",
    "cofounders_details", "company_founded_date", "startup_description", "team_unique",
    "current_customers", "goals_next_6_months", "funding_from_whom", "website_link",
    "participated_accelerator", "heard_about_us", "additional_info",
]
CHOICE_FIELDS = {
    "primary_sector": SECTORS,
    "startup_stage": STAGES,
    "cofounders_count": list(COFOUNDERS),
    "time_working_on_startup": list(TIME_WORKING),
    "raised_funding": YES_NO,
    "revenue_past_year": list(REVENUE),
}
REQUIRED = ["full_name", "email", "linkedin", "phone", "role_in_company", "company_name",
            "primary_sector", "startup_stage", "cofounders_count", "time_working_on_startup"]
MAX_LEN = 2000
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate(form) -> tuple[dict, dict]:
    """Return (clean_data, errors). `form` is a Flask MultiDict."""
    data, errors = {}, {}

    for name in TEXT_FIELDS:
        value = (form.get(name) or "").strip()
        if len(value) > MAX_LEN:
            errors[name] = f"Please keep this under {MAX_LEN} characters."
        data[name] = value[:MAX_LEN]

    for name, allowed in CHOICE_FIELDS.items():
        value = form.get(name) or ""
        if value and value not in allowed:
            errors[name] = "Please choose one of the listed options."
        data[name] = value if value in allowed else ""

    gains = [g for g in form.getlist("gain") if g in GAINS]
    data["gain_from_program"] = ", ".join(gains)

    for name in REQUIRED:
        if not data.get(name):
            errors.setdefault(name, "This field is required.")
    if not gains:
        errors["gain"] = "Choose at least one option."
    if data["email"] and not EMAIL_RE.match(data["email"]):
        errors["email"] = "Please enter a valid email address."
    if form.get("consent") != "on":
        errors["consent"] = "Consent is required to submit."
    return data, errors
