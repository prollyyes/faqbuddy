from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .AuthAPI import router as auth_router
from .Search import router as search_router
from .Profile import router as profile_router
from .Chat import router as chat_router
from .model_manager import model_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events for the FastAPI app."""
    print("====== STARTUP: Loading models... ======")
    # Load the primary model on startup
    model_manager.load_mistral()
    yield
    print("====== SHUTDOWN: Unloading models... ======")
    model_manager.unload_all()

app = FastAPI(title="api", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.faqbuddy.net",
        "https://faqbuddy.net",
        "https://faqbuddy.vercel.app",
        "https://faqbuddy-frontend.vercel.app",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(search_router)
app.include_router(profile_router)
app.include_router(chat_router) 



# just for testing purposes
@app.get("/test")
def test_endpoint():
    return {"message": "Test successful!"}
