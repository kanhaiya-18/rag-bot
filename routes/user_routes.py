from fastapi import APIRouter,status,UploadFile,File,Depends,Request,BackgroundTasks
from services.users_services import create_user,login,user_details
from schemas.users import userCreate,userResponse,userLogin,authMW,QuestionSchema,RenameChatSchema
from services.uploadFile_services import upload_file,get_pdfs,delete_pdf
from helpers.is_auth_helper import is_auth
from services.response_services import ask_question,get_users_chat,get_history,delete_chat,rename_chat

userRouter = APIRouter()

@userRouter.post("/create",status_code=status.HTTP_201_CREATED)
async def create_user_route(user: userCreate):
    return await create_user(user)

@userRouter.post("/login",status_code=status.HTTP_200_OK)
async def login_route(user: userLogin):
    return await login(user)

@userRouter.get("/user-details",status_code=status.HTTP_200_OK)
async def user_details_route(user:authMW = Depends(is_auth)):
    return await user_details(user)

@userRouter.post("/upload-file",status_code=status.HTTP_201_CREATED)
async def upload_file_route(background_task: BackgroundTasks,file: UploadFile=File(...),user:authMW = Depends(is_auth)):
    return  await upload_file(background_task,user,file)

@userRouter.post("/ask-question")
async def ask_question_route(request:Request,question: QuestionSchema,user: authMW = Depends(is_auth)):
    return await ask_question(request.app.state.graph,user,question)

@userRouter.get("/get-users-chat",status_code=status.HTTP_200_OK)
async def get_users_chat_route(user: authMW = Depends(is_auth)):
    return await get_users_chat(user)

@userRouter.get("/get-chat/{thread_id}",status_code=status.HTTP_200_OK)
async def get_history_route(request: Request,thread_id: str,user: authMW = Depends(is_auth)):
    return await get_history(request.app.state.graph,thread_id,user)


@userRouter.get("/get-pdfs",status_code=status.HTTP_200_OK)
async def get_pdfs_route(user: authMW = Depends(is_auth)):
    return await get_pdfs(user)

@userRouter.delete("/delete-pdf/{file_id}",status_code=status.HTTP_200_OK)
async def delete_pdf_route(file_id:str,user: authMW = Depends(is_auth)):
    return await delete_pdf(file_id,user)

@userRouter.delete("/delete-chat/{thread_id}",status_code=status.HTTP_200_OK)
async def delete_chat_route(thread_id: str,user: authMW = Depends(is_auth)):
    return await delete_chat(thread_id,user)

@userRouter.put("/rename-chat/{thread_id}",status_code=status.HTTP_200_OK)
async def rename_chat_route(thread_id: str,body: RenameChatSchema,user: authMW = Depends(is_auth)):
    return await rename_chat(thread_id,body.title,user)