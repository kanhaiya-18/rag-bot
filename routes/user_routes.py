from fastapi import APIRouter,status,UploadFile,File,Depends,Request
from services.users_services import create_user,login
from schemas.users import userCreate,userResponse,userLogin,authMW,QuestionSchema
from services.uploadFile_services import upload_file
from helpers.is_auth_helper import is_auth
from services.response_services import ask_question,get_users_chat,get_history

userRouter = APIRouter(prefix="/user")

@userRouter.post("/create",status_code=status.HTTP_201_CREATED)
async def create_user_route(user: userCreate):
    return await create_user(user)

@userRouter.post("/login",status_code=status.HTTP_200_OK)
async def login_route(user: userLogin):
    return await login(user)

@userRouter.post("/upload-file",status_code=status.HTTP_201_CREATED)
async def upload_file_route(file: UploadFile=File(...),user:authMW = Depends(is_auth)):
    return  await upload_file(user,file)

@userRouter.post("/ask-question")
async def ask_question_route(request:Request,question: QuestionSchema,user: authMW = Depends(is_auth)):
    return await ask_question(request.app.state.graph,user,question)

@userRouter.get("/get-users-chat",status_code=status.HTTP_200_OK)
async def get_users_chat_route(user: authMW = Depends(is_auth)):
    return await get_users_chat(user)

@userRouter.get("/get-chat/{thread_id}",status_code=status.HTTP_200_OK)
async def get_history_route(request: Request,thread_id: str,user: authMW = Depends(is_auth)):
    return await get_history(request.app.state.graph,thread_id,user)