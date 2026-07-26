from contextlib import asynccontextmanager
from fastapi import FastAPI
from routes.user_routes import userRouter
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from core.config import settings
from helpers.graph import builder
from fastapi.middleware.cors import CORSMiddleware

checkpointer = AsyncPostgresSaver.from_conn_string(
    settings.POSTGRES_URL
)

@asynccontextmanager
async def lifespan(app: FastAPI):


    async with AsyncPostgresSaver.from_conn_string(
        settings.POSTGRES_URL
    ) as checkpointer:

        await checkpointer.setup()

        app.state.graph = builder.compile(
            checkpointer=checkpointer
        )

        yield
origins = "http://localhost:5173/"
app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(userRouter)
