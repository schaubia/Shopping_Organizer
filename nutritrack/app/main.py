from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.routers import predict, ingredients, shopping, spending, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all DB tables on startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="NutriTrack API",
    description="Food recognition, nutrition analysis, shopping & spending optimization",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,        prefix="/auth",      tags=["Auth"])
app.include_router(predict.router,     prefix="/predict",   tags=["Food Recognition"])
app.include_router(ingredients.router, prefix="/ingredients", tags=["Ingredients"])
app.include_router(shopping.router,    prefix="/shopping",  tags=["Shopping List"])
app.include_router(spending.router,    prefix="/spending",  tags=["Spending"])


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}
