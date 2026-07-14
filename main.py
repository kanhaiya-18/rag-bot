from fastapi import FastAPI
from routes.user_routes import userRouter
app = FastAPI()
app.include_router(userRouter)
@app.get("/")
async def home():
    return {"msg" : "hello"}