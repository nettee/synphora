from enum import Enum
from pydantic import BaseModel


class EventType(Enum):
    RUN_STARTED = "RUN_STARTED"
    RUN_FINISHED = "RUN_FINISHED"
    TEXT_MESSAGE = "TEXT_MESSAGE"

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
