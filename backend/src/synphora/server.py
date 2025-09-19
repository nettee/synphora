from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime
from typing import List

from synphora.agent import AgentRequest, generate_agent_response
from synphora.sse import SseEvent
from synphora.agent import get_suggestions

app = FastAPI(title="Synphora Agent Server", version="1.0.0")

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # 允许前端端口访问
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有头部
)


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

class SuggestionResponse(BaseModel):
    suggestions: List[str]

@app.get("/health", response_model=HealthResponse)
async def api_health():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )

@app.get("/suggestions", response_model=SuggestionResponse)
async def api_suggestions():
    """Get chat suggestions from environment variables"""
    suggestions = get_suggestions()
    return SuggestionResponse(suggestions=suggestions)

@app.post("/agent")
async def api_agent(request: AgentRequest):
    """Streaming agent endpoint"""

    print(f'receive /agent request: {request}')

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
