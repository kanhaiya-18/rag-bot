from fastapi import APIRouter,status,UploadFile,File
from services.users_services import create_user,login
from schemas.users import userCreate,userResponse,userLogin


userRouter = APIRouter(prefix="/user")

@userRouter.post("/create",status_code=status.HTTP_201_CREATED)
async def create_user_route(user: userCreate):
    return await create_user(user)

@userRouter.post("/login",status_code=status.HTTP_200_OK)
async def login_route(user: userLogin):
    return await login(user)

    