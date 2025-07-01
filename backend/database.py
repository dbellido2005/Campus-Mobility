# database.py
from motor.motor_asyncio import AsyncIOMotorClient
import os

mongoURI = "mongodb+srv://***REMOVED***@cluster0.t5pt5k6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MONGO_URI = os.getenv("MONGO_URI", mongoURI)
client = AsyncIOMotorClient(MONGO_URI)
db = client["your_db_name"]

users_collection = db["users"]
rides_collection = db["ride_requests"]
