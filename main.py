from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select
from database.db import create_db_and_tables
from database.db import SessionDep
from database.models import User
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("📋 Táblák létrehozása...")
    create_db_and_tables()
    print("✅ Táblák létrehozva!")
    yield


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root(session: SessionDep):
    statement = select(User)
    users = session.exec(statement).all()
    return users
