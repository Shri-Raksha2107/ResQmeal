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


def score_label(score: int, hours: int, packaging: str) -> str:
    """Return a human-readable safety label based on the numerical score."""
    if hours > 12 and packaging == "open":
        return "Not Recommended"
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 50:
        return "Acceptable"
    return "Not Recommended"


def analyze_food_safety_ai(food_name: str, hours: int, temp: str, packaging: str) -> str:
    """
    Query Gemini for a detailed food safety analysis. 
    Returns a short markdown string.
    """
    import google.generativeai as genai
    from config import Config

    if not Config.GEMINI_API_KEY:
        return ""

    try:
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = (
            f"You are a food safety expert. I am donating '{food_name}'. "
            f"It will be stored at {temp} temperature in {packaging} packaging for {hours} hours.\n"
            "Provide a brief (2-3 sentences max) food safety advisory. Mention any specific risks for this type of food and storage conditions."
        )
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini Food Safety AI Error: {e}")
        return ""


def score_details(score: int, hours: int, packaging: str) -> dict:
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
