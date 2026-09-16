from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.api.router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(router, prefix="/api")
