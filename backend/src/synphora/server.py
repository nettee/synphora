from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime

from synphora.agent import AgentRequest, generate_agent_response
from synphora.sse import SseEvent

app = FastAPI(title="Synphora Agent Server", version="1.0.0")


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

@app.post("/agent")
async def agent_stream(request: AgentRequest):
    """Streaming agent endpoint"""

    def format_sse_event(event: SseEvent) -> str:
        return f"data: {event.to_data()}\n\n"

    async def generate_sse():
        async for event in generate_agent_response(request):
            yield format_sse_event(event)

    return StreamingResponse(
        generate_sse(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )
