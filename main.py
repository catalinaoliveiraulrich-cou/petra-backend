from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import re
import requests
from typing import Optional, Tuple, List, Dict

from rentcast_api import get_rental_listings

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

    return ("Austin", "TX")  # fallback


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


def extract_lifestyle_preferences(query: str) -> Dict[str, bool]:
    text = query.lower()

    prefs = {
        "near_cafes": False,
        "near_gyms": False,
        "near_parks": False,
        "near_public_transport": False,
        "walkable": False,
    }

    if any(term in text for term in ["cafe", "cafes", "coffee", "coffee shop", "coffee shops"]):
        prefs["near_cafes"] = True

    if any(term in text for term in ["gym", "gyms", "fitness", "workout"]):
        prefs["near_gyms"] = True

    if any(term in text for term in ["park", "parks", "green space"]):
        prefs["near_parks"] = True

    if any(term in text for term in ["public transport", "transit", "subway", "metro", "bus", "train"]):
        prefs["near_public_transport"] = True

    if any(term in text for term in ["walkable", "walking distance", "walk everywhere"]):
        prefs["walkable"] = True

    return prefs


def get_nearby_places(lat: float, lng: float, place_type: str, radius: float = 800.0):
    if not GOOGLE_PLACES_API_KEY:
        raise ValueError("Missing GOOGLE_PLACES_API_KEY")

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

    if not response.ok:
        raise ValueError(f"Google Places error {response.status_code}: {response.text}")

    data = response.json()
    return data.get("places", [])


def analyze_neighborhood(lat: float, lng: float) -> Dict[str, int]:
    cafes = get_nearby_places(lat, lng, "cafe")
    gyms = get_nearby_places(lat, lng, "gym")
    parks = get_nearby_places(lat, lng, "park")
    transit = get_nearby_places(lat, lng, "transit_station")

    total_places = len(cafes) + len(gyms) + len(parks) + len(transit)

    return {
        "cafe_count": len(cafes),
        "gym_count": len(gyms),
        "park_count": len(parks),
        "transit_count": len(transit),
        "walkability_hint": total_places,
    }


def score_listing(
    listing: dict,
    budget: Optional[int],
    beds: Optional[int],
    pets: Optional[bool],
    lifestyle: Dict[str, bool],
    neighborhood: Dict[str, int],
) -> int:
    score = 0

    price = listing.get("price")
    listing_beds = listing.get("bedrooms")

    if budget is not None and isinstance(price, (int, float)):
        if price <= budget:
            score += 3
        elif price <= budget + 200:
            score += 1

    if beds is not None and listing_beds is not None:
        if listing_beds == beds:
            score += 3
        elif abs(listing_beds - beds) == 1:
            score += 1

    # Pet friendliness is not always available in RentCast data.
    # For now, only add score if the user requested pets and listing explicitly says so.
    listing_pet_friendly = listing.get("petFriendly")
    if pets is True and listing_pet_friendly is True:
        score += 2

    if lifestyle.get("near_cafes") and neighborhood["cafe_count"] > 0:
        score += 1
    if lifestyle.get("near_gyms") and neighborhood["gym_count"] > 0:
        score += 1
    if lifestyle.get("near_parks") and neighborhood["park_count"] > 0:
        score += 1
    if lifestyle.get("near_public_transport") and neighborhood["transit_count"] > 0:
        score += 1
    if lifestyle.get("walkable") and neighborhood["walkability_hint"] >= 3:
        score += 1

    return score


def build_reasons(
    city: str,
    listing: dict,
    budget: Optional[int],
    beds: Optional[int],
    pets: Optional[bool],
    lifestyle: Dict[str, bool],
    neighborhood: Dict[str, int],
) -> List[str]:
    reasons = []

    price = listing.get("price")
    listing_beds = listing.get("bedrooms")

    reasons.append(f"Located in {city}")

    if budget is not None and isinstance(price, (int, float)):
        if price <= budget:
            reasons.append("Within your budget")
        elif price <= budget + 200:
            reasons.append("Close to your budget")

    if beds is not None and listing_beds == beds:
        if beds == 0:
            reasons.append("Matches your studio preference")
        else:
            reasons.append(f"Matches your {beds}-bedroom preference")

    listing_pet_friendly = listing.get("petFriendly")
    if pets is True and listing_pet_friendly is True:
        reasons.append("Pet-friendly")

    if lifestyle.get("near_cafes") and neighborhood["cafe_count"] > 0:
        reasons.append(f"{neighborhood['cafe_count']} cafes nearby")

    if lifestyle.get("near_gyms") and neighborhood["gym_count"] > 0:
        reasons.append(f"{neighborhood['gym_count']} gyms nearby")

    if lifestyle.get("near_parks") and neighborhood["park_count"] > 0:
        reasons.append(f"{neighborhood['park_count']} parks nearby")

    if lifestyle.get("near_public_transport") and neighborhood["transit_count"] > 0:
        reasons.append(f"{neighborhood['transit_count']} transit options nearby")

    if lifestyle.get("walkable") and neighborhood["walkability_hint"] >= 3:
        reasons.append("In a more walkable area")

    return reasons[:3]


def build_tradeoff(
    listing: dict,
    budget: Optional[int],
    beds: Optional[int],
    lifestyle: Dict[str, bool],
    neighborhood: Dict[str, int],
) -> str:
    price = listing.get("price")
    listing_beds = listing.get("bedrooms")

    if budget is not None and isinstance(price, (int, float)) and price > budget:
        return "Slightly above your preferred budget."

    if beds is not None and listing_beds is not None and listing_beds < beds:
        return "Fewer bedrooms than requested."

    if lifestyle.get("near_public_transport") and neighborhood["transit_count"] == 0:
        return "Not especially close to public transport."

    if lifestyle.get("near_parks") and neighborhood["park_count"] == 0:
        return "Not especially close to parks."

    if lifestyle.get("near_cafes") and neighborhood["cafe_count"] == 0:
        return "Not especially close to cafes."

    return "Slightly smaller living area."


@app.get("/")
def home():
    return {"message": "Petra backend is working!"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/debug-env")
def debug_env():
    return {
        "has_google_places_key": GOOGLE_PLACES_API_KEY is not None,
        "google_places_key_length": len(GOOGLE_PLACES_API_KEY) if GOOGLE_PLACES_API_KEY else 0,
    }

@app.get("/debug-rentcast")
def debug_rentcast():
    city = "Miami"
    state = "FL"
    listings = get_rental_listings(city=city, state=state, limit=1)
    return {
        "count": len(listings) if isinstance(listings, list) else 0,
        "first_listing": listings[0] if listings else None,
    }

@app.get("/test-places")
def test_places():
    lat, lng = 30.2672, -97.7431  # Austin test location
    try:
        return analyze_neighborhood(lat, lng)
    except Exception as e:
        return {
            "error": str(e),
            "has_google_places_key": GOOGLE_PLACES_API_KEY is not None,
            "google_places_key_length": len(GOOGLE_PLACES_API_KEY) if GOOGLE_PLACES_API_KEY else 0,
        }


@app.post("/search")
def search(payload: SearchRequest):
    city, state = extract_city_state(payload.query)
    budget = extract_budget(payload.query)
    beds = extract_bedrooms(payload.query)
    pets = extract_pets(payload.query)
    lifestyle = extract_lifestyle_preferences(payload.query)

    try:
        listings = get_rental_listings(city=city, state=state, limit=5)
    except Exception as e:
        return {
            "summary": f"I couldn’t fetch live listings for {city}, {state}.",
            "error": f"RentCast error: {str(e)}",
            "matches": [],
        }

    if not listings:
        return {
            "summary": f"I couldn’t find live listings for {city}, {state}.",
            "matches": [],
        }

    enriched_matches = []

    for listing in listings:
        try:
            lat = listing.get("latitude")
            lng = listing.get("longitude")

            neighborhood = {
                "cafe_count": 0,
                "gym_count": 0,
                "park_count": 0,
                "transit_count": 0,
                "walkability_hint": 0,
            }

            if isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
                try:
                    neighborhood = analyze_neighborhood(lat, lng)
                except Exception:
                    pass

            score = score_listing(
                listing=listing,
                budget=budget,
                beds=beds,
                pets=pets,
                lifestyle=lifestyle,
                neighborhood=neighborhood,
            )

            enriched_matches.append(
                {
                    "title": listing.get("formattedAddress")
                    or listing.get("address")
                    or f"{city} listing",
                    "price": listing.get("price"),
                    "beds": listing.get("bedrooms"),
                    "baths": listing.get("bathrooms"),
                    "reasons": build_reasons(
                        city=city,
                        listing=listing,
                        budget=budget,
                        beds=beds,
                        pets=pets,
                        lifestyle=lifestyle,
                        neighborhood=neighborhood,
                    ),
                    "tradeoff": build_tradeoff(
                        listing=listing,
                        budget=budget,
                        beds=beds,
                        lifestyle=lifestyle,
                        neighborhood=neighborhood,
                    ),
                    "_score": score,
                }
            )
        except Exception as e:
            print("Error processing listing:", listing)
            print("Listing error:", e)

    enriched_matches.sort(key=lambda x: x["_score"], reverse=True)

    final_matches = []
    for match in enriched_matches[:3]:
        match.pop("_score", None)
        final_matches.append(match)

    summary_parts = [f"Here are a few places that seem like a good fit in {city}, {state}"]

    if budget is not None:
        summary_parts.append(f"around your budget of ${budget}")
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
            "lifestyle": lifestyle,
        },
        "matches": final_matches,
    }
