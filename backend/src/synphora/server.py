from datetime import datetime

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from synphora.agent import AgentRequest, generate_agent_response
from synphora.artifact_manager import artifact_manager
from synphora.models import ArtifactData, ArtifactRole, ArtifactType
from synphora.sse import EventType, SseEvent

app = FastAPI(title="Synphora Agent Server", version="1.0.0")

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],  # 允许前端端口访问
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有头部
)


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


class CreateArtifactRequest(BaseModel):
    title: str
    content: str
    description: str | None = None


class ArtifactListResponse(BaseModel):
    artifacts: list[ArtifactData]


@app.get("/health", response_model=HealthResponse)
async def api_health():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy", timestamp=datetime.now().isoformat(), version="1.0.0"
    )


@app.post("/agent")
async def api_agent(request: AgentRequest):
    """Streaming agent endpoint"""

    print(f'receive /agent request: {request}')

    def format_sse_event(event: SseEvent) -> str:
        return f"data: {event.to_data()}\n\n"

    async def generate_sse():
        async for event in generate_agent_response(request):
            if event.type not in (
                EventType.TEXT_MESSAGE,
                EventType.ARTIFACT_CONTENT_CHUNK,
            ):
                print(f'send sse event: {event}')
            yield format_sse_event(event)

    return StreamingResponse(
        generate_sse(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        },
    )


@app.get("/artifacts", response_model=ArtifactListResponse)
async def get_artifacts():
    """Get all artifacts"""
    print("📋 Starting get_artifacts operation")
    artifacts = artifact_manager.list_artifacts()
    print(f"✅ get_artifacts completed, found {len(artifacts)} artifacts")
    return ArtifactListResponse(artifacts=artifacts)


@app.post("/artifacts", response_model=ArtifactData)
async def create_artifact(request: CreateArtifactRequest):
    """Create a new artifact"""
    print(f"📝 Starting create_artifact operation for title '{request.title}'")
    artifact = artifact_manager.create_artifact(
        title=request.title,
        content=request.content,
        description=request.description,
        role=ArtifactRole.USER,
        artifact_type=ArtifactType.ORIGINAL,
    )
    print(f"✅ create_artifact completed, artifact ID: {artifact.id}")
    return artifact


@app.post("/artifacts/upload", response_model=ArtifactData)
async def upload_artifact(file: UploadFile = File(...)):
    """Upload a file as an artifact"""
    print(f"📤 Starting upload_artifact operation for file '{file.filename}'")
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    content = await file.read()
    content_str = content.decode('utf-8')

    artifact = artifact_manager.create_artifact(
        title=file.filename,
        content=content_str,
        role=ArtifactRole.USER,
        artifact_type=ArtifactType.ORIGINAL,
    )
    print(
        f"✅ upload_artifact completed, file '{file.filename}' saved as artifact ID: {artifact.id}"
    )
    return artifact


@app.get("/artifacts/{artifact_id}", response_model=ArtifactData)
async def get_artifact(artifact_id: str):
    """Get a specific artifact by ID"""
    print(f"🔍 Starting get_artifact operation for ID '{artifact_id}'")
    artifact = artifact_manager.get_artifact(artifact_id)
    if not artifact:
        print(f"❌ get_artifact failed, artifact ID '{artifact_id}' not found")
        raise HTTPException(status_code=404, detail="Artifact not found")
    print(f"✅ get_artifact completed, found artifact '{artifact.title}'")
    return artifact


@app.delete("/artifacts/{artifact_id}")
async def delete_artifact(artifact_id: str):
    """Delete an artifact"""
    print(f"🗑️ Starting delete_artifact operation for ID '{artifact_id}'")
    success = artifact_manager.delete_artifact(artifact_id)
    if not success:
        print(f"❌ delete_artifact failed, artifact ID '{artifact_id}' not found")
        raise HTTPException(status_code=404, detail="Artifact not found")
    print(f"✅ delete_artifact completed, artifact ID '{artifact_id}' deleted")
    return {"message": "Artifact deleted successfully"}
