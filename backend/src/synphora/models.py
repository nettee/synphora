from typing import Optional
from pydantic import BaseModel
from enum import Enum


class ArtifactType(str, Enum):
    ORIGINAL = "original"
    COMMENT = "comment"


class ArtifactData(BaseModel):
    id: str
    role: str  # "user" | "assistant" 
    type: ArtifactType
    title: str
    description: Optional[str] = None
    content: str
    created_at: str
    updated_at: str