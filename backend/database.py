# database.py
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = AsyncIOMotorClient(MONGO_URI)
db = client["your_db_name"]

users_collection = db["users"]
rides_collection = db["ride_requests"]
group_chats_collection = db["group_chats"]
questions_collection = db["questions"]
private_responses_collection = db["private_responses"]
reports_collection = db["user_reports"]
