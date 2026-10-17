"""Fit Score: a transparent 0-10 ranking of how well an application matches the program.

The program targets post-MVP, Pre-Seed and Seed startups that want to enter the U.S. market.
The weights below are my own assumptions, chosen to reflect that profile. They have not
been validated against which startups were accepted or succeeded, so the score is a
triage aid for reviewers, not a decision.
"""

STAGE_POINTS = {"Pre-Seed": 2, "Seed": 2, "Early revenue": 1, "Ideation": 0}

# Teams that have worked 6-24 months usually have an MVP but are still early enough for the
# program. Teams past two years without moving beyond Seed get fewer points.
TIME_POINTS = {"lt_3": 0, "3_6": 2, "6_24": 4, "gt_24": 2}

MAX_SCORE = 10


def fit_score(app: dict) -> int:
    score = STAGE_POINTS.get(app.get("startup_stage"), 0)

    try:
        founders = int(app.get("cofounders_count") or 0)
    except (TypeError, ValueError):
        founders = 0
    score += 2 if founders >= 2 else 1 if founders == 1 else 0

    score += TIME_POINTS.get(app.get("time_working_on_startup"), 0)
    score += 1 if (app.get("current_customers") or "").strip() else 0
    score += 1 if app.get("raised_funding") == "Yes" else 0
    return score


def score_band(score: int) -> str:
    return "high" if score >= 7 else "mid" if score >= 4 else "low"
