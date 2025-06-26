from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.AuthAPI import router as auth_router
from src.api.Search import router as search_router

app = FastAPI(title="api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(search_router)
