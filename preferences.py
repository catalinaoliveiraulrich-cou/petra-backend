"""
preferences.py

This simple file stores user preferences for PetraAI.
Everything is kept in basic Python variables and a dictionary
so it is easy to read and change for beginners.
"""

# ----------------------------------------
# Basic preference variables
# ----------------------------------------

# The city where the user wants to live or search for places.
city = "San Francisco"

# Minimum budget in your local currency.
budget_min = 1500

# Maximum budget in your local currency.
budget_max = 3000

# Number of bedrooms you prefer.
bedrooms = 2

# Whether pets are allowed.
# Use True if pets are allowed, or False if they are not.
pets_allowed = True

# Commute preference description.
# You can write anything like:
# "short commute", "near public transport", "remote work", etc.
commute_preference = "short commute"


# ----------------------------------------
# Grouping preferences in a dictionary
# ----------------------------------------

# This dictionary collects all of the preferences in one place.
# A dictionary in Python stores data as key–value pairs.
# For example: "city" is the key and the value is whatever is in the city variable.
preferences = {
    "city": city,
    "budget_min": budget_min,
    "budget_max": budget_max,
    "bedrooms": bedrooms,
    "pets_allowed": pets_allowed,
    "commute_preference": commute_preference,
}


def get_preferences():
    """
    Return all preferences as a dictionary.

    Other parts of the PetraAI program can import this function
    and call get_preferences() to read the user's current settings.
    """
    return preferences


if __name__ == "__main__":
    # If you run this file directly with:
    #   python preferences.py
    # it will print the preferences to the screen.
    print("Current PetraAI preferences:")
    print(preferences)

