from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Petra backend is working!"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/search")
def search():
    return {
        "summary": "Here are a few places that seem like a good fit.",
        "matches": [
            {
                "title": "Downtown Austin Apartment",
                "price": 2100,
                "beds": 1,
                "baths": 1,
                "reasons": [
                    "Pet-friendly",
                    "Within your budget"
                ],
                "tradeoff": "Slightly smaller living area."
            }
        ]
    }