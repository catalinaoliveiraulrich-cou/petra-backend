from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import re
import requests
from typing import Optional, Tuple


load_dotenv()

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    query: str


def extract_city_state(query: str) -> Tuple[str, str]:
    text = query.lower()

    city_map = {
        "austin": ("Austin", "TX"),
        "new york": ("New York", "NY"),
        "miami": ("Miami", "FL"),
        "chicago": ("Chicago", "IL"),
        "los angeles": ("Los Angeles", "CA"),
        "san francisco": ("San Francisco", "CA"),
        "boston": ("Boston", "MA"),
        "seattle": ("Seattle", "WA"),
        "atlanta": ("Atlanta", "GA"),
        "dallas": ("Dallas", "TX"),
    }

    for city_name, value in city_map.items():
        if city_name in text:
            return value

    return ("Austin", "TX")  # fallback for now


def extract_budget(query: str) -> Optional[int]:
    text = query.lower().replace(",", "")

    patterns = [
        r"under\s+\$?(\d+)",
        r"max(?:imum)?\s+\$?(\d+)",
        r"up to\s+\$?(\d+)",
        r"budget\s+(?:is\s+)?\$?(\d+)",
        r"\$ ?(\d+)\s+max",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))

    dollar_matches = re.findall(r"\$ ?(\d+)", text)
    if dollar_matches:
        return int(dollar_matches[0])

    return None


def extract_bedrooms(query: str) -> Optional[int]:
    text = query.lower()

    patterns = [
        r"(\d+)\s*(?:bed|bedroom|br|bd)\b",
        r"(\d+)[-\s]?(?:bed|bedroom|br|bd)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))

    word_map = {
        "studio": 0,
        "one bedroom": 1,
        "1 bedroom": 1,
        "two bedroom": 2,
        "2 bedroom": 2,
        "three bedroom": 3,
        "3 bedroom": 3,
    }

    for phrase, value in word_map.items():
        if phrase in text:
            return value

    return None


def extract_pets(query: str) -> Optional[bool]:
    text = query.lower()

    pet_positive_keywords = [
        "pet friendly",
        "pets allowed",
        "allows pets",
        "dog friendly",
        "cat friendly",
        "i have a dog",
        "i have a cat",
        "with my dog",
        "with my cat",
        "pet-friendly",
    ]

    pet_negative_keywords = [
        "no pets",
        "not pet friendly",
        "pets not allowed",
        "without pets",
    ]

    for phrase in pet_negative_keywords:
        if phrase in text:
            return False

    for phrase in pet_positive_keywords:
        if phrase in text:
            return True

    if any(word in text for word in ["dog", "cat", "pet", "pets"]):
        return True

    return None


def build_reasons(
    city: str,
    budget: Optional[int],
    beds: Optional[int],
    pets: Optional[bool],
    price: int,
    listing_beds: int,
):
    reasons = [f"Located in {city}"]

    if budget is not None and price <= budget:
        reasons.append("Within your budget")
    elif budget is not None and price <= budget + 200:
        reasons.append("Close to your budget")

    if beds is not None and listing_beds == beds:
        if beds == 0:
            reasons.append("Matches your studio preference")
        else:
            reasons.append(f"Matches your {beds}-bedroom preference")

    if pets is True:
        reasons.append("Pet-friendly")

    return reasons[:3]


def build_tradeoff(
    budget: Optional[int],
    price: int,
    beds: Optional[int],
    listing_beds: int,
):
    if budget is not None and price > budget:
        return "Slightly above your preferred budget."
    if beds is not None and listing_beds < beds:
        return "Fewer bedrooms than requested."
    if beds is not None and listing_beds > beds:
        return "More space than requested, which may increase the price."
    return "Slightly smaller living area."


def get_nearby_places(
    lat: float,
    lng: float,
    place_type: str,
    radius: float = 800.0,
):
    if not GOOGLE_PLACES_API_KEY:
        return []

    url = "https://places.googleapis.com/v1/places:searchNearby"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.primaryType,places.location",
    }

    body = {
        "includedTypes": [place_type],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": lat,
                    "longitude": lng,
                },
                "radius": radius,
            }
        },
    }

    response = requests.post(url, headers=headers, json=body, timeout=20)
    response.raise_for_status()
    data = response.json()
    return data.get("places", [])


def analyze_neighborhood(lat: float, lng: float):
    cafes = get_nearby_places(lat, lng, "cafe")
    gyms = get_nearby_places(lat, lng, "gym")
    parks = get_nearby_places(lat, lng, "park")
    transit = get_nearby_places(lat, lng, "transit_station")

    return {
        "near_cafes": len(cafes) > 0,
        "cafe_count": len(cafes),
        "near_gyms": len(gyms) > 0,
        "gym_count": len(gyms),
        "near_parks": len(parks) > 0,
        "park_count": len(parks),
        "near_public_transport": len(transit) > 0,
        "transit_count": len(transit),
    }


@app.get("/")
def home():
    return {"message": "Petra backend is working!"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/test-places")
def test_places():
    lat, lng = 30.2672, -97.7431  # Austin test location
    return analyze_neighborhood(lat, lng)


@app.post("/search")
def search(payload: SearchRequest):
    city, state = extract_city_state(payload.query)
    budget = extract_budget(payload.query)
    beds = extract_bedrooms(payload.query)
    pets = extract_pets(payload.query)

    listing_1_price = budget - 100 if budget and budget > 1200 else 2100
    listing_2_price = budget + 150 if budget else 2300

    listing_1_beds = beds if beds is not None else 1
    listing_2_beds = beds + 1 if beds is not None else 2

    summary_parts = [f"Here are a few places that seem like a good fit in {city}, {state}"]

    if budget is not None:
        summary_parts.append(f"under about ${budget}")
    if beds is not None:
        if beds == 0:
            summary_parts.append("matching your studio preference")
        else:
            summary_parts.append(f"matching your {beds}-bedroom preference")
    if pets is True:
        summary_parts.append("with pet-friendly options")

    summary = ", ".join(summary_parts) + "."

    return {
        "summary": summary,
        "parsed_preferences": {
            "city": city,
            "state": state,
            "budget_max": budget,
            "bedrooms": beds,
            "pets": pets,
        },
        "matches": [
            {
                "title": f"{city} Apartment 1",
                "price": listing_1_price,
                "beds": listing_1_beds,
                "baths": 1,
                "reasons": build_reasons(
                    city,
                    budget,
                    beds,
                    pets,
                    listing_1_price,
                    listing_1_beds,
                ),
                "tradeoff": build_tradeoff(
                    budget,
                    listing_1_price,
                    beds,
                    listing_1_beds,
                ),
            },
            {
                "title": f"{city} Apartment 2",
                "price": listing_2_price,
                "beds": listing_2_beds,
                "baths": 1,
                "reasons": build_reasons(
                    city,
                    budget,
                    beds,
                    pets,
                    listing_2_price,
                    listing_2_beds,
                ),
                "tradeoff": build_tradeoff(
                    budget,
                    listing_2_price,
                    beds,
                    listing_2_beds,
                ),
            },
        ],
    }
    