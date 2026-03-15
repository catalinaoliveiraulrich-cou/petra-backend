from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re

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


def extract_city_state(query: str):
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
        "dallas": ("Dallas", "TX")
    }

    for city_name, value in city_map.items():
        if city_name in text:
            return value

    return ("Austin", "TX")  # fallback for now


@app.get("/")
def home():
    return {"message": "Petra backend is working!"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/search")
def search(payload: SearchRequest):
    city, state = extract_city_state(payload.query)

    return {
        "summary": f"Here are a few places that seem like a good fit in {city}, {state}.",
        "matches": [
            {
                "title": f"{city} Apartment 1",
                "price": 2100,
                "beds": 1,
                "baths": 1,
                "reasons": [
                    f"Located in {city}",
                    "Within your budget"
                ],
                "tradeoff": "Slightly smaller living area."
            },
            {
                "title": f"{city} Apartment 2",
                "price": 2300,
                "beds": 2,
                "baths": 1,
                "reasons": [
                    f"Located in {city}",
                    "Good fit for your preferences"
                ],
                "tradeoff": "A bit above your ideal price."
            }
        ]
    }