from contextlib import asynccontextmanager
from fastapi import FastAPI
from routes.user_routes import userRouter
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from core.config import settings
from helpers.graph import builder
from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Initialize rate limiter using client IP address
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

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

origins = ["https://rag-chat-bot-client.vercel.app", "http://10.147.189.8:5173"]

app = FastAPI(lifespan=lifespan)

# Attach rate-limiter to application state & register middleware & exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(userRouter)
