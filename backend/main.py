from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx
from routes import users, rides, places
from dotenv import load_dotenv

# Load environment variables from .env file
import os
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
print(f"DEBUG: Environment variables loaded. GOOGLE_PLACES_API_KEY: {os.getenv('GOOGLE_PLACES_API_KEY', 'NOT SET')[:10] if os.getenv('GOOGLE_PLACES_API_KEY') else 'NOT SET'}...")
print(f"DEBUG: Current working directory: {os.getcwd()}")
print(f"DEBUG: Script directory: {os.path.dirname(__file__)}")
print(f"DEBUG: .env file path: {os.path.join(os.path.dirname(__file__), '.env')}")
print(f"DEBUG: .env file exists: {os.path.exists(os.path.join(os.path.dirname(__file__), '.env'))}")

app = FastAPI()

# Database
app.include_router(users.router)
app.include_router(rides.router)
app.include_router(places.router)

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

