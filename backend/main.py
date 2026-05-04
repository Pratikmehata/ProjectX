from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os

# Allow importing from src folder
sys.path.insert(0, os.path.dirname(__file__))

from src.main_engine import PCRecommendationEngine

app = FastAPI(
    title="PC Build Recommender API",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load engine once
data_path = os.path.join(os.path.dirname(__file__), "data")
engine = PCRecommendationEngine(data_path)


# ------------------------
# Request Model
# ------------------------
class RecommendationRequest(BaseModel):
    query: str
    budget: int
    resolution: str


# ------------------------
# Routes
# ------------------------

@app.get("/")
def root():
    return {
        "name": "PC Build Recommender API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "engine_loaded": engine is not None
    }


@app.get("/api/resolutions")
def get_resolutions():
    return {
        "resolutions": ["1080p", "1440p", "4K"]
    }


@app.post("/api/recommend")
def recommend(request: RecommendationRequest):
    try:
        result = engine.recommend(
            request.query,
            request.budget,
            request.resolution
        )

        return {
            "type": result.get("type", "recommendation"),
            "message": result.get("message", "No recommendation generated"),
            "components": result.get("components"),
            "total_price": result.get("total_price"),
            "performance_estimate": (
                "High" if request.budget > 100000
                else "Medium" if request.budget > 50000
                else "Entry"
            )
        }

    except Exception as e:
        return {
            "type": "error",
            "message": str(e)
        }


# ------------------------
# Run Server Directly
# ------------------------
if __name__ == "__main__":
    import uvicorn
    print("Starting PC Build Recommender API...")
    print("Access the API at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )