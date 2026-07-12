"""
services/safety_score.py

AI Food Safety Scoring algorithm.  Pure Python – mirrors the frontend JS
formula so results are consistent between client preview and server record.
"""


def compute_safety_score(
    meals: int,
    hours: int,
    temperature: str,
    packaging: str,
) -> int:
    """
    Compute a food-safety score in the range [18, 98].

    Parameters
    ----------
    meals       : number of meal portions available
    hours       : hours the food remains safe
    temperature : 'hot' | 'room' | 'cold'
    packaging   : 'sealed' | 'covered' | 'open'

    Returns
    -------
    int : safety score (higher = safer / better for donation)
    """
    score: float = 54 + hours * 7 + min(meals / 25, 8)

    if temperature == "cold":
        score += 8
    elif temperature == "hot":
        score += 5

    if packaging == "sealed":
        score += 12
    elif packaging == "covered":
        score += 4
    elif packaging == "open":
        score -= 24

    if hours <= 1:
        score -= 12

    return int(max(18, min(98, round(score))))


def score_label(score: int, hours: int, packaging: str) -> dict:
    """
    Return a human-readable decision dict based on the score.

    Returns
    -------
    dict with keys: title, details, badge, badge_style
    """
    if score < 45:
        return {
            "title": "AI Food Safety Score: Needs review",
            "details": (
                "Open or low-time food should be checked before matching. "
                "The app can pause alerts until admin approval."
            ),
            "badge": "Manual review",
            "badge_style": "hot",
        }
    if hours <= 1:
        return {
            "title": "AI Food Safety Score: Emergency pickup",
            "details": (
                "Food is acceptable but urgent. "
                "Volunteers within the smallest radius are notified first."
            ),
            "badge": "Emergency alert",
            "badge_style": "warn",
        }
    pkg_word = "Sealed" if packaging == "sealed" else "Covered"
    return {
        "title": "AI Food Safety Score: Good to donate",
        "details": (
            f"{pkg_word} food with {hours} hours remaining is safe for fast pickup. "
            "NGOs with matching demand are prioritised."
        ),
        "badge": "Approved for rescue",
        "badge_style": "green",
    }
