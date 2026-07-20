from core.config import settings
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = settings.DATABASE_URL

client = AsyncIOMotorClient(MONGO_URL)



db = client["ragbot"]

user_collection = db["users"]
documets = db["documents"]


async def get_db():
    return db