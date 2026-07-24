from contextlib import asynccontextmanager
from fastapi import FastAPI
from routes.user_routes import userRouter
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from core.config import settings
from helpers.graph import builder

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

app = FastAPI(lifespan=lifespan)

app.include_router(userRouter)