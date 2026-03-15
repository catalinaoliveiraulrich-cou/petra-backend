"""
ranking.py

This file defines a simple scoring function for PetraAI.
The function is called `petra_score` and it gives an apartment
an overall score from 0 to 100 based on:
    - budget fit
    - location fit
    - amenities fit

The goal is to keep the code very beginner-friendly.
"""


def petra_score(budget_fit, location_fit, amenities_fit):
    """
    Calculate a PetraAI score for an apartment.

    Each input should be a number between 0 and 100:
        budget_fit:    how well the price matches the user's budget
        location_fit:  how good the location is for the user
        amenities_fit: how well the amenities match what the user wants

    The function returns a single score between 0 and 100.

    For now, we use a very simple method:
        - take the average of the three inputs
        - make sure the final score is between 0 and 100

    This makes it easy to change the formula later if needed.
    """

    # Step 1: Put all the individual scores into a list.
    # This makes it easy to work with them together.
    scores = [budget_fit, location_fit, amenities_fit]

    # Step 2: Calculate the average of the scores.
    # sum(scores) adds them all up.
    # len(scores) is how many scores there are (here it is 3).
    average_score = sum(scores) / len(scores)

    # Step 3: Make sure the final score is between 0 and 100.
    # If the average goes below 0, we clamp it up to 0.
    # If it goes above 100, we clamp it down to 100.
    if average_score < 0:
        final_score = 0
    elif average_score > 100:
        final_score = 100
    else:
        final_score = average_score

    # Step 4: Return the final score.
    return final_score


if __name__ == "__main__":
    # This block runs only if you execute this file directly:
    #   python ranking.py
    #
    # It gives a quick example of how `petra_score` works.

    example_budget_fit = 80      # good price
    example_location_fit = 70    # decent location
    example_amenities_fit = 90   # excellent amenities

    score = petra_score(
        example_budget_fit,
        example_location_fit,
        example_amenities_fit,
    )

    print("Example PetraAI score:", score)

