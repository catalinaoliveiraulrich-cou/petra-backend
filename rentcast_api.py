"""
rentcast_api.py

This file shows a very simple, beginner-friendly example of how to:
    - load the RentCast API key from a .env file
    - call the rental listings endpoint
    - fetch listings by city and state
    - print a few useful fields for each listing

Before running this file, make sure you:
1. Have `requests` and `python-dotenv` installed:
       pip install requests python-dotenv
2. Have a `.env` file in the same folder with a line like:
       RENTCAST_API_KEY=your_real_api_key_here
"""

import os

import requests
from dotenv import load_dotenv


# ----------------------------------------
# Load API key from .env
# ----------------------------------------

# This reads key–value pairs from the `.env` file into environment variables.
load_dotenv()

# Now we can read the API key using os.getenv.
API_KEY = os.getenv("RENTCAST_API_KEY")

# Base URL for the RentCast API.
BASE_URL = "https://api.rentcast.io/v1"


def get_rental_listings(city, state, limit=5):
    """
    Call the RentCast rental listings endpoint and return the results as JSON.

    Parameters
    ----------
    city : str
        City name to search in (for example: "Austin").
    state : str
        State code (for example: "TX").
    limit : int
        Maximum number of listings to fetch.
    """

    # Check that we actually have an API key.
    if not API_KEY:
        raise ValueError("Missing RENTCAST_API_KEY in .env file")

    # This is the endpoint for long-term rental listings.
    url = f"{BASE_URL}/listings/rental/long-term"

    # RentCast expects the API key in this header.
    headers = {
        "X-Api-Key": API_KEY,
    }

    # Query parameters we send to the API.
    params = {
        "city": city,
        "state": state,
        "limit": limit,
    }

    # Send the HTTP GET request.
    # timeout=20 means it will wait up to 20 seconds for a response.
    response = requests.get(url, headers=headers, params=params, timeout=20)

    # If the API returns an error code (like 400 or 500),
    # this line will raise an exception with details.
    response.raise_for_status()

    # Return the parsed JSON data (usually a list of listings).
    return response.json()


def print_listings_summary(listings):
    """
    Print a few useful fields for each listing in a friendly way.

    We try to be defensive and use .get() so the code will not crash
    if a field is missing in the API response.
    """
    if not listings:
        print("No listings found.")
        return

    print(f"Found {len(listings)} listing(s):")
    print()

    for i, listing in enumerate(listings, start=1):
        # These field names are based on the RentCast API docs.
        address = listing.get("formattedAddress") or listing.get("address")
        price = listing.get("price")
        beds = listing.get("bedrooms")
        baths = listing.get("bathrooms")
        sqft = listing.get("squareFootage") or listing.get("squareFeet")
        property_type = listing.get("propertyType")

        print(f"Listing #{i}")
        print(f"  Address:       {address}")
        print(f"  Price:         ${price} / month")
        print(f"  Beds/Baths:    {beds} bd / {baths} ba")
        print(f"  Square Feet:   {sqft}")
        print(f"  Property Type: {property_type}")
        print("-" * 40)


if __name__ == "__main__":
    # Example usage of the RentCast helper functions.
    #
    # You can change "Austin" and "TX" to your own city and state.
    example_city = "Austin"
    example_state = "TX"

    print(f"Requesting rental listings for {example_city}, {example_state}...")

    try:
        listings_data = get_rental_listings(example_city, example_state, limit=3)
        # In many cases, the API returns a list directly.
        # If it returns a dictionary, you might need to access a field like
        # listings_data["data"]. Adjust this as needed based on your actual response.
        if isinstance(listings_data, dict):
            # Try a common pattern: look for a "data" field, fall back to an empty list.
            listings = listings_data.get("data", [])
        else:
            listings = listings_data

        print_listings_summary(listings)
    except Exception as e:
        # For a real app, you would handle errors more carefully.
        # Here we just print the error so beginners can see what went wrong.
        print("Error while calling RentCast API:", e)
