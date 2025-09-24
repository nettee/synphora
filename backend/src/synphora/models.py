from enum import Enum

from pydantic import BaseModel


class ArtifactType(str, Enum):
    ORIGINAL = "original"
    COMMENT = "comment"


class ArtifactRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ArtifactData(BaseModel):
    id: str
    role: ArtifactRole
    type: ArtifactType
    title: str
    description: str | None = None
    content: str
    created_at: str
    updated_at: str


class EvaluateType(str, Enum):
    COMMENT = "comment"
    TITLE = "title"
    INTRODUCTION = "introduction"
