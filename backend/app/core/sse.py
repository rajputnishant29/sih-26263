import asyncio
import json
from typing import Set, Dict, Any
from starlette.responses import StreamingResponse
from fastapi import Request


class SSEManager:
    """
    Native async Server-Sent Events broker for real-time dashboard and review queue synchronization.
    Sends standard event stream text lines: 'event: ...\ndata: ...\n\n'
    """
    def __init__(self):
        self._queues: Set[asyncio.Queue] = set()

    async def event_generator(self, request: Request):
        queue = asyncio.Queue()
        self._queues.add(queue)

        # Initial keepalive / connection confirmation
        yield "event: connected\ndata: {}\n\n"

        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=20.0)
                    event_name = data.get("event", "update")
                    payload = json.dumps(data.get("payload", {}))
                    yield f"event: {event_name}\ndata: {payload}\n\n"
                except asyncio.TimeoutError:
                    # Send periodic ping keepalive
                    yield "event: ping\ndata: {}\n\n"
        finally:
            if queue in self._queues:
                self._queues.remove(queue)

    def as_response(self, request: Request) -> StreamingResponse:
        return StreamingResponse(
            self.event_generator(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    def broadcast(self, event: str, payload: Dict[str, Any]):
        message = {"event": event, "payload": payload}
        for queue in list(self._queues):
            try:
                queue.put_nowait(message)
            except Exception:
                pass


sse_manager = SSEManager()
