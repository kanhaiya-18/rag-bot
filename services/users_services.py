from db.database import user_collection
from schemas.users import userCreate,userLogin
from fastapi import HTTPException
import jwt
from pwdlib import PasswordHash
from datetime import datetime,timedelta,timezone
from core.config import settings
password_hash = PasswordHash.recommended()

def get_password_hash(password):
    return password_hash.hash(password)

def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)
async def create_user(user: userCreate):
    try:
        #check if user already exist 
        userExist = await user_collection.find_one({"email" : user.email})
        if userExist: 
            raise HTTPException(409,detail="user already exist")
        
        hash_password = get_password_hash(user.password)
        user.password = hash_password
        response = await user_collection.insert_one(user.model_dump())
        id = str(response.inserted_id)
        #hash the password
        
        #generate jwt token 
        expires = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        # print(expires)
        payload = {"_id" : id,"exp" : expires}
        token = jwt.encode(payload,settings.SECRET_KEY,algorithm=settings.ALGORITHM)
        data = user.model_dump()
        data["id"] = id
        # print(token)
        return {"token" : token}
        
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(500,detail="something went wrong")
async def login(user:userLogin):
    #check if the user exist
    userExist = await user_collection.find_one({"email" : user.email})
    if not userExist: 
        raise HTTPException(401,detail="user doesnt exist")
    
    match = verify_password(user.password,userExist["password"])
    if not match:
        raise HTTPException(401,detail="password is wrong")
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # print(expires)
    # print(userExist["_id"])
    payload = {"_id" : str(userExist["_id"]),"exp" : expires}
    token = jwt.encode(payload,settings.SECRET_KEY,algorithm=settings.ALGORITHM)
    return {"token" : token}
    
async def user_details(user):
    userExist = await user_collection.find_one({"email" : user.get("email")})
    if not userExist: 
        raise HTTPException(401,detail="user doesnt exist")
    # print(user)
    return user
        
    
