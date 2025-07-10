from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx
from routes import users, rides, places, communities, messaging
from dotenv import load_dotenv

# Load environment variables from .env file
import os
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

app = FastAPI()

# Database
app.include_router(users.router)
app.include_router(rides.router)
app.include_router(places.router)
app.include_router(communities.router)
app.include_router(messaging.router)

# Frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later, set this to your real frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping")
def ping():
    return {"message": "pong"}

   
#UBER API

#UBER_API_URL = "https://api.uber.com/v1.2/estimates/price"
#UBER_ACCESS_TOKEN = "YOUR_UBER_ACCESS_TOKEN"  # Replace with your token

