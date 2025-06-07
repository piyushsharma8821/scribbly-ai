from fastapi import FastAPI
from app.users import router as user_router
from app.routes import router as notes_router
from app.chat_with_notes import router as chat_router
from app.graphql import graphql_app

app = FastAPI(title="Notes API")

app.include_router(user_router)
app.include_router(notes_router)
app.include_router(graphql_app, prefix="/graphql")
app.include_router(chat_router)