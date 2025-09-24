from enum import Enum

from pydantic import BaseModel


class EventType(Enum):
    RUN_STARTED = "RUN_STARTED"
    RUN_FINISHED = "RUN_FINISHED"
    TEXT_MESSAGE = "TEXT_MESSAGE"
    ARTIFACT_LIST_UPDATED = "ARTIFACT_LIST_UPDATED"
    ARTIFACT_CONTENT_START = "ARTIFACT_CONTENT_START"
    ARTIFACT_CONTENT_CHUNK = "ARTIFACT_CONTENT_CHUNK"
    ARTIFACT_CONTENT_COMPLETE = "ARTIFACT_CONTENT_COMPLETE"


class SseEvent(BaseModel):
    type: EventType

    def to_data(self) -> str:
        return self.model_dump_json(exclude_none=True)


class RunStartedEvent(SseEvent):
    def __init__(self):
        super().__init__(type=EventType.RUN_STARTED)

    @classmethod
    def new(cls) -> "RunStartedEvent":
        return cls()


class RunFinishedEvent(SseEvent):
    def __init__(self):
        super().__init__(type=EventType.RUN_FINISHED)

    @classmethod
    def new(cls) -> "RunFinishedEvent":
        return cls()


class TextMessageData(BaseModel):
    message_id: str
    content: str


class TextMessageEvent(SseEvent):
    data: TextMessageData

    def __init__(self, **kwargs):
        super().__init__(type=EventType.TEXT_MESSAGE, **kwargs)

    @classmethod
    def new(cls, message_id: str, content: str) -> "TextMessageEvent":
        return cls(data=TextMessageData(message_id=message_id, content=content))


class ArtifactListUpdatedData(BaseModel):
    artifact_id: str
    title: str
    artifact_type: str
    role: str


class ArtifactListUpdatedEvent(SseEvent):
    data: ArtifactListUpdatedData

    def __init__(self, **kwargs):
        super().__init__(type=EventType.ARTIFACT_LIST_UPDATED, **kwargs)

    @classmethod
    def new(
        cls, artifact_id: str, title: str, artifact_type: str, role: str
    ) -> "ArtifactListUpdatedEvent":
        return cls(
            data=ArtifactListUpdatedData(
                artifact_id=artifact_id,
                title=title,
                artifact_type=artifact_type,
                role=role,
            )
        )


class ArtifactContentStartData(BaseModel):
    artifact_id: str
    title: str
    artifact_type: str


class ArtifactContentStartEvent(SseEvent):
    data: ArtifactContentStartData

    def __init__(self, **kwargs):
        super().__init__(type=EventType.ARTIFACT_CONTENT_START, **kwargs)

    @classmethod
    def new(
        cls, artifact_id: str, title: str, artifact_type: str
    ) -> "ArtifactContentStartEvent":
        return cls(
            data=ArtifactContentStartData(
                artifact_id=artifact_id, title=title, artifact_type=artifact_type
            )
        )


class ArtifactContentChunkData(BaseModel):
    artifact_id: str
    content: str


class ArtifactContentChunkEvent(SseEvent):
    data: ArtifactContentChunkData

    def __init__(self, **kwargs):
        super().__init__(type=EventType.ARTIFACT_CONTENT_CHUNK, **kwargs)

    @classmethod
    def new(cls, artifact_id: str, content: str) -> "ArtifactContentChunkEvent":
        return cls(
            data=ArtifactContentChunkData(artifact_id=artifact_id, content=content)
        )


class ArtifactContentCompleteData(BaseModel):
    artifact_id: str


class ArtifactContentCompleteEvent(SseEvent):
    data: ArtifactContentCompleteData

    def __init__(self, **kwargs):
        super().__init__(type=EventType.ARTIFACT_CONTENT_COMPLETE, **kwargs)

    @classmethod
    def new(cls, artifact_id: str) -> "ArtifactContentCompleteEvent":
        return cls(data=ArtifactContentCompleteData(artifact_id=artifact_id))
