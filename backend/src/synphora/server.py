from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, AsyncGenerator
import json
import asyncio
from datetime import datetime

app = FastAPI(title="Synphora Agent Server", version="1.0.0")

class AgentRequest(BaseModel):
    text: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )

async def generate_agent_response(request: AgentRequest) -> AsyncGenerator[str, None]:
    """Simulate streaming agent response"""
    response_text = f"Processing your message: '{request.text}'"
    words = response_text.split()
    
    for i, word in enumerate(words):
        data = {
            "type": "token",
            "content": word + " ",
            "index": i,
            "finished": False
        }
        yield f"data: {json.dumps(data)}\n\n"
        await asyncio.sleep(0.1)  # Simulate processing delay
    
    # Send completion signal
    completion_data = {
        "type": "completion",
        "content": "",
        "finished": True,
        "metadata": {
            "total_tokens": len(words),
            "processing_time": len(words) * 0.1
        }
    }
    yield f"data: {json.dumps(completion_data)}\n\n"

@app.post("/agent")
async def agent_stream(request: AgentRequest):
    """Streaming agent endpoint"""
    return StreamingResponse(
        generate_agent_response(request),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )
