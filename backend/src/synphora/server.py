from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

from synphora.agent import AgentRequest, generate_agent_response
from synphora.sse import SseEvent
from synphora.agent import get_suggestions
from synphora.artifact_manager import artifact_manager
from synphora.models import ArtifactData, ArtifactType

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

class CreateArtifactRequest(BaseModel):
    title: str
    content: str
    description: Optional[str] = None

class ArtifactListResponse(BaseModel):
    artifacts: List[ArtifactData]

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

@app.get("/artifacts", response_model=ArtifactListResponse)
async def get_artifacts():
    """Get all artifacts"""
    artifacts = artifact_manager.list_artifacts()
    return ArtifactListResponse(artifacts=artifacts)

@app.post("/artifacts", response_model=ArtifactData)
async def create_artifact(request: CreateArtifactRequest):
    """Create a new artifact"""
    artifact = artifact_manager.create_artifact(
        title=request.title,
        content=request.content,
        description=request.description,
        role="user",
        artifact_type=ArtifactType.ORIGINAL
    )
    return artifact

@app.post("/artifacts/upload", response_model=ArtifactData)
async def upload_artifact(file: UploadFile = File(...)):
    """Upload a file as an artifact"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    content = await file.read()
    content_str = content.decode('utf-8')
    
    artifact = artifact_manager.create_artifact(
        title=file.filename,
        content=content_str,
        role="user",
        artifact_type=ArtifactType.ORIGINAL
    )
    return artifact

@app.get("/artifacts/{artifact_id}", response_model=ArtifactData)
async def get_artifact(artifact_id: str):
    """Get a specific artifact by ID"""
    artifact = artifact_manager.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact

@app.delete("/artifacts/{artifact_id}")
async def delete_artifact(artifact_id: str):
    """Delete an artifact"""
    success = artifact_manager.delete_artifact(artifact_id)
    if not success:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {"message": "Artifact deleted successfully"}
