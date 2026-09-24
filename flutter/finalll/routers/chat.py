import uuid
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from schemas import ChatRequest, Location

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
def chat(req: ChatRequest, request: Request):
    conversation_id = req.conversation_id or f"conv_{uuid.uuid4().hex[:10]}"
    result = request.app.state.orca.run(req.message, conversation_id, req.location)
    return result.model_dump()


@router.websocket("/ws/{conversation_id}")
async def chat_ws(websocket: WebSocket, conversation_id: str):
    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_json()
            message = str(payload.get("message", "")).strip()
            if not message:
                await websocket.send_json({"error": "message is required"})
                continue
            loc = Location.model_validate(payload["location"]) if payload.get("location") else None
            result = websocket.app.state.orca.run(message, conversation_id, loc)
            await websocket.send_json(result.model_dump())
    except WebSocketDisconnect:
        pass
