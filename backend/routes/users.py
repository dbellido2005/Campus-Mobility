# routes/users.py
from fastapi import APIRouter
from models import User
from database import users_collection

router = APIRouter()

@router.post("/users")
async def create_user(user: User):
    result = await users_collection.insert_one(user.dict())
    return {"id": str(result.inserted_id), **user.dict()}

@router.get("/users")
async def list_users():
    users = []
    cursor = users_collection.find({})
    async for user in cursor:
        user["_id"] = str(user["_id"])
        users.append(user)
    return users
