"""
chat_flow.py

This file shows a very simple demo flow for PetraAI.

Steps:
1. Create user preferences.
2. Create 3 fake apartment listings.
3. Score them using the PetraAI ranking function.
4. Print the best match and a short explanation.

Everything is written in beginner-friendly Python.
"""

from preferences import (
    city,
    budget_min,
    budget_max,
    bedrooms,
    pets_allowed,
    commute_preference,
)
from ranking import petra_score
from explanation import explain_apartment


def create_user_preferences():
    """
    Create a simple dictionary with the user's preferences.

    In a real chat flow, these might come from user answers.
    Here we just reuse the values from `preferences.py`.
    """
    return {
        "city": city,
        "budget_min": budget_min,
        "budget_max": budget_max,
        "bedrooms": bedrooms,
        "pets_allowed": pets_allowed,
        "commute_preference": commute_preference,
    }


def create_fake_apartments():
    """
    Create 3 fake apartment listings for the demo.

    Each apartment is a dictionary with basic information.
    """
    a1 = {
        "name": "Sunny Studio Downtown",
        "price": 2200,
        "bedrooms": 1,
        "pets_allowed": True,
        "location_note": "Very close to public transport and offices.",
        "amenities_note": "Has a small balcony and lots of light.",
    }

    a2 = {
        "name": "Cozy 2BR in Quiet Area",
        "price": 2600,
        "bedrooms": 2,
        "pets_allowed": True,
        "location_note": "Quiet neighborhood, 25-minute commute.",
        "amenities_note": "Includes parking and in-unit laundry.",
    }

    a3 = {
        "name": "Spacious 3BR Suburban Home",
        "price": 3200,
        "bedrooms": 3,
        "pets_allowed": False,
        "location_note": "Farther from the city, 45-minute commute.",
        "amenities_note": "Large backyard and extra storage.",
    }

    return [a1, a2, a3]


def simple_budget_fit(price, user_prefs):
    """
    Return a budget fit score between 0 and 100.

    This is a very simple rule-based scoring:
    - 100 if price is inside [budget_min, budget_max]
    - 70 if price is a little below budget_min
    - 50 if price is a little above budget_max
    - 20 otherwise
    """
    low = user_prefs["budget_min"]
    high = user_prefs["budget_max"]

    if low <= price <= high:
        return 100
    elif price < low and price >= low * 0.9:
        return 70
    elif price > high and price <= high * 1.1:
        return 50
    else:
        return 20


def simple_location_fit(apartment, user_prefs):
    """
    Return a location fit score between 0 and 100.

    For this demo, we only look at a text note.
    In real life, you would use maps, distance, etc.
    """
    note = apartment["location_note"].lower()

    # Very simple keyword-based rules.
    if "10 minute" in note or "very close" in note or "downtown" in note:
        return 90
    elif "25-minute" in note or "25 minute" in note:
        return 70
    elif "45-minute" in note or "45 minute" in note or "farther" in note:
        return 50
    else:
        return 60  # default medium score


def simple_amenities_fit(apartment, user_prefs):
    """
    Return an amenities fit score between 0 and 100.

    We look at:
    - bedrooms compared to user preference
    - whether pets are allowed if the user has pets
    """
    score = 0
    parts = 0

    # Bedrooms comparison.
    desired_bedrooms = user_prefs["bedrooms"]
    if apartment["bedrooms"] == desired_bedrooms:
        score += 90
    elif apartment["bedrooms"] == desired_bedrooms + 1:
        score += 80
    elif apartment["bedrooms"] == desired_bedrooms - 1:
        score += 70
    else:
        score += 60
    parts += 1

    # Pet policy.
    if user_prefs["pets_allowed"]:
        # User wants pets allowed.
        if apartment["pets_allowed"]:
            score += 100
        else:
            score += 40
        parts += 1

    # If we did not add any parts (very unlikely here), avoid division by zero.
    if parts == 0:
        return 50

    return score / parts


def main():
    """
    Run the simple chat flow demo.
    """
    # 1. Create user preferences.
    user_prefs = create_user_preferences()

    # 2. Create 3 fake apartment listings.
    apartments = create_fake_apartments()

    # 3. Score them.
    scored_apartments = []
    for apt in apartments:
        budget_fit = simple_budget_fit(apt["price"], user_prefs)
        location_fit = simple_location_fit(apt, user_prefs)
        amenities_fit = simple_amenities_fit(apt, user_prefs)

        score = petra_score(budget_fit, location_fit, amenities_fit)

        scored_apartments.append(
            {
                "apartment": apt,
                "score": score,
                "budget_fit": budget_fit,
                "location_fit": location_fit,
                "amenities_fit": amenities_fit,
            }
        )

    # 4. Find and print the best match.
    best = max(scored_apartments, key=lambda x: x["score"])
    best_apt = best["apartment"]

    # Build a simple explanation text using our helper.
    match_reason = (
        f"It matches many of your preferences in {user_prefs['city']} "
        f"with {best_apt['bedrooms']} bedroom(s) and a location that fits your commute."
    )

    # Describe a tradeoff in a friendly way.
    tradeoff = "You may want to double-check the exact neighborhood and size to be sure it feels right."

    # Price information text.
    price_text = (
        f"The price is ${best_apt['price']} per month, "
        f"while your budget range is ${user_prefs['budget_min']}–${user_prefs['budget_max']}."
    )

    explanation = explain_apartment(match_reason, tradeoff, price_text)

    # Print results.
    print("=== PetraAI Simple Demo ===")
    print()
    print("User preferences:", user_prefs)
    print()
    print("Scored apartments:")
    for item in scored_apartments:
        print(
            f"- {item['apartment']['name']}: "
            f"score={item['score']:.1f} "
            f"(budget={item['budget_fit']:.1f}, "
            f"location={item['location_fit']:.1f}, "
            f"amenities={item['amenities_fit']:.1f})"
        )
    print()
    print("Best match:", best_apt["name"])
    print(explanation)


if __name__ == "__main__":
    main()

