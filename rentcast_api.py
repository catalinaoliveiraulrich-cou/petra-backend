"""
rentcast_api.py

Simple helper for fetching rental listings from the RentCast API.
"""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv


# Load environment variables from .env in the same folder
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("RENTCAST_API_KEY")
BASE_URL = "https://api.rentcast.io/v1"


def get_rental_listings(city: str, state: str, limit: int = 5):
    """
    Fetch long-term rental listings from RentCast.

    Parameters
    ----------
    city : str
        City name, for example "Austin"
    state : str
        State code, for example "TX"
    limit : int
        Maximum number of listings to return
    """
    if not API_KEY:
        raise ValueError("Missing RENTCAST_API_KEY in .env file")

    url = f"{BASE_URL}/listings/rental/long-term"

    headers = {
        "X-Api-Key": API_KEY,
    }

    params = {
        "city": city,
        "state": state,
        "limit": limit,
    }

    response = requests.get(url, headers=headers, params=params, timeout=20)
    response.raise_for_status()

    data = response.json()

    # Some APIs return a list directly, others wrap it in a dict
    if isinstance(data, dict):
        return data.get("data", [])
    return data


def print_listings_summary(listings):
    """
    Print a simple summary of listings for debugging.
    """
    if not listings:
        print("No listings found.")
        return

    print(f"Found {len(listings)} listing(s):\n")

    for i, listing in enumerate(listings, start=1):
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
    example_city = "Austin"
    example_state = "TX"

    print(f"Requesting rental listings for {example_city}, {example_state}...")

    try:
        listings = get_rental_listings(example_city, example_state, limit=3)
        print_listings_summary(listings)
    except Exception as e:
        print("Error while calling RentCast API:", e)
        
