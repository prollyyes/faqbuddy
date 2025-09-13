from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .AuthAPI import router as auth_router
from .Search import router as search_router
from .Profile import router as profile_router
from .Chat import router as chat_router 

app = FastAPI(title="api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.faqbuddy.net",
        "https://faqbuddy.net",
        "https://faqbuddy.vercel.app",
        "https://faqbuddy-frontend.vercel.app",
        "http://localhost:3000",
        "http://localhost:3001",
        "https://localhost:3000",
        "https://localhost:3001"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(search_router)
app.include_router(profile_router)
app.include_router(chat_router) 



# Health check endpoint for Render
@app.get("/")
def root():
    return {"message": "FAQBuddy API is running!", "status": "healthy"}

# just for testing purposes
@app.get("/test")
def test_endpoint():
    return {"message": "Test successful!"}

# Environment and system status endpoint
@app.get("/status")
def system_status():
    import os
    return {
        "message": "System status check",
        "remote_llm_base": os.getenv("REMOTE_LLM_BASE", "NOT SET"),
        "remote_llm_model": os.getenv("REMOTE_LLM_MODEL", "NOT SET"),
        "remote_llm_key": "SET" if os.getenv("REMOTE_LLM_API_KEY") else "NOT SET",
        "status": "healthy"
    }
