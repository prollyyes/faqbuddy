from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
import sys
import os
import json
from pathlib import Path

# Add the project root to the Python path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

from rag_core import RAGSystem

app = FastAPI(title="FAQ Buddy API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG system
rag = RAGSystem(
    model_name="all-MiniLM-L6-v2",
    index_name="exams-index",
    namespace="v2"
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    retrieval_time: float
    generation_time: float
    total_time: float

async def stream_response(query: str):
    """Stream the response token by token."""
    try:
        # Get the response with timing info
        result = rag.generate_response_streaming(query)
        
        # Send timing information first
        timing_data = {
            "type": "timing",
            "retrieval_time": result["retrieval_time"],
            "generation_time": result["generation_time"],
            "total_time": result["total_time"]
        }
        yield f"data: {json.dumps(timing_data)}\n\n"
        
        # Stream the response tokens
        for token in result["response_stream"]:
            token_data = {
                "type": "token",
                "token": token
            }
            yield f"data: {json.dumps(token_data)}\n\n"
        
        # Send end signal
        end_data = {
            "type": "end"
        }
        yield f"data: {json.dumps(end_data)}\n\n"
        
    except Exception as e:
        error_data = {
            "type": "error",
            "error": str(e)
        }
        yield f"data: {json.dumps(error_data)}\n\n"

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint."""
    return StreamingResponse(
        stream_response(request.message),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Non-streaming chat endpoint for backward compatibility."""
    try:
        result = rag.generate_response(request.message)
        return ChatResponse(
            response=result["response"],
            retrieval_time=result["retrieval_time"],
            generation_time=result["generation_time"],
            total_time=result["total_time"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class HealthCheck(BaseModel):
    status: str
    message: str

@app.get("/api/health", response_model=HealthCheck)
async def health_check():
    return HealthCheck(status="ok", message="Service is running") 