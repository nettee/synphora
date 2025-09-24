from langgraph.config import get_stream_writer

from synphora.sse import SseEvent


def write_sse_event(event: SseEvent):
    writer = get_stream_writer()
    if writer:
        writer({"channel": "sse", "type": event.type.value, "event": event})
