"""
explanation.py

This file defines a simple function for PetraAI that explains:
    - why an apartment is a good match
    - one tradeoff
    - price information

The function returns a short text explanation that can be shown to a user.
The code is written in a very beginner-friendly style.
"""


def explain_apartment(match_reason, tradeoff, price_text):
    """
    Build a human-readable explanation for an apartment.

    Parameters
    ----------
    match_reason : str
        A short sentence about why this apartment is a good match.
        Example: "It is close to your office and allows pets."

    tradeoff : str
        One main downside or thing to be aware of.
        Example: "The kitchen is a bit small."

    price_text : str
        A short description of the price.
        Example: "$2,500 per month, which is within your budget."

    Returns
    -------
    str
        A multi-line explanation string that combines all of the parts.
    """

    # We build the explanation step by step using simple string operations.

    # Start with why it is a good match.
    explanation = "Why this apartment is a good match:\n"
    explanation += f"- {match_reason}\n"

    # Add the tradeoff line.
    explanation += "Main tradeoff:\n"
    explanation += f"- {tradeoff}\n"

    # Add the price information line.
    explanation += "Price information:\n"
    explanation += f"- {price_text}"

    # Return the final explanation string.
    return explanation


if __name__ == "__main__":
    # This example only runs when you execute this file directly:
    #   python explanation.py
    #
    # It shows what a finished explanation might look like.

    example_match_reason = "It is 10 minutes from your office and allows pets."
    example_tradeoff = "The apartment is slightly smaller than your ideal size."
    example_price_text = "$2,400 per month, which is within your budget range."

    text = explain_apartment(
        example_match_reason,
        example_tradeoff,
        example_price_text,
    )

    print(text)

