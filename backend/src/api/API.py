from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .AuthAPI import router as auth_router
from .Search import router as search_router
from .Profile import router as profile_router
#from .Chat import router as chat_router

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
app.include_router(profile_router)
#app.include_router(chat_router)
