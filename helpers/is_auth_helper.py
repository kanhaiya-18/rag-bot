from fastapi import Request,HTTPException,Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
import jwt
from core.config import settings
from bson import ObjectId
# from db.database import user_collection
from db.database import get_db
async def is_auth(request:Request,db: AsyncIOMotorDatabase=Depends(get_db)):
    user_collection = db["users"]
    token = request.headers.get("Authorization")
    if not token : 
        raise HTTPException(400,detail="token is not sent")
    token = token.split(" ")[1]
    try : 
        payload = jwt.decode(token,settings.SECRET_KEY,algorithms=[settings.ALGORITHM])
    except Exception as e:
        raise HTTPException(401, detail="unauthorized user")
    user = await user_collection.find_one({"_id" : ObjectId(payload.get("_id"))})
    if not user: 
        raise HTTPException(401, detail="unauthorized user")
    # print(user)
    
    return user