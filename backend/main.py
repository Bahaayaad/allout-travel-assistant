import asyncio
import json
import os
import uuid
import re
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from agents.supervisor_agent import root_agent
from database import init_db, resolve_escalation, get_pending_escalations
from services.email_service import parse_supervisor_reply

APP_NAME = "allout_travel"
DEBOUNCE_SECS = 2.5

session_service = InMemorySessionService()
message_buffer = defaultdict(list)
buffer_timers = {}
sse_queues = defaultdict(list)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("Database ready")
    yield


app = FastAPI(title="Allout Travel API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    conversation_id: str | None = None
    message: str


class SupervisorReply(BaseModel):
    escalation_id: str
    response: str
    conversation_id: str


class EmailWebhook(BaseModel):
    subject: str = ""
    text: str = ""
    html: str = ""
    headers: str = ""


async def run_agent(conv_id: str, message: str) -> str:
    session = await session_service.get_session(
        app_name=APP_NAME, user_id="user", session_id=conv_id
    )
    if not session:
        session = await session_service.create_session(
            app_name=APP_NAME, user_id="user", session_id=conv_id
        )

    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)
    content = genai_types.Content(role="user", parts=[genai_types.Part(text=message)])

    response = ""
    async for event in runner.run_async(user_id="user", session_id=conv_id, new_message=content):
        if event.is_final_response() and event.content and event.content.parts:
            response = event.content.parts[0].text or ""

    return response or "Sorry, something went wrong. Please try again."


async def broadcast(conv_id: str, data: dict):
    for q in sse_queues.get(conv_id, []):
        await q.put(data)


async def flush_buffer(conv_id: str):
    await asyncio.sleep(DEBOUNCE_SECS)

    msgs = message_buffer.pop(conv_id, [])
    if not msgs:
        return

    combined = " ".join(msgs)
    await broadcast(conv_id, {"type": "typing"})

    reply = await run_agent(conv_id, combined)
    await broadcast(conv_id, {"type": "message", "role": "assistant", "content": reply})
    buffer_timers.pop(conv_id, None)


@app.post("/api/chat")
async def chat(payload: ChatMessage):
    conv_id = payload.conversation_id or str(uuid.uuid4())
    msg = payload.message.strip()

    if not msg:
        raise HTTPException(status_code=400, detail="Empty message")

    message_buffer[conv_id].append(msg)

    existing = buffer_timers.get(conv_id)
    if existing and not existing.done():
        existing.cancel()

    buffer_timers[conv_id] = asyncio.create_task(flush_buffer(conv_id))
    return {"conversation_id": conv_id}


@app.get("/api/stream/{conv_id}")
async def stream(conv_id: str):
    q = asyncio.Queue()
    sse_queues[conv_id].append(q)

    async def generate():
        try:
            yield f"data: {json.dumps({'type': 'connected'})}\n\n"
            while True:
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=30)
                    yield f"data: {json.dumps(msg)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'ping'})}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if q in sse_queues[conv_id]:
                sse_queues[conv_id].remove(q)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@app.post("/api/supervisor/reply")
async def supervisor_reply(payload: SupervisorReply):
    resolve_escalation(payload.escalation_id, payload.response)
    await broadcast(payload.conversation_id, {
        "type": "message",
        "role": "supervisor",
        "content": payload.response,
        "escalation_id": payload.escalation_id
    })
    return {"ok": True}


@app.post("/api/webhook/email")
async def email_webhook(payload: EmailWebhook):
    esc_id = ""
    conv_id = ""

    for line in payload.headers.split("\n"):
        if line.startswith("X-Escalation-ID:"):
            esc_id = line.split(":", 1)[1].strip()
        elif line.startswith("X-Conversation-ID:"):
            conv_id = line.split(":", 1)[1].strip()

    if not esc_id:
        match = re.search(r"ESC-[A-Z0-9]+", payload.subject)
        if match:
            esc_id = match.group()

    if not esc_id:
        raise HTTPException(400, "Could not find escalation ID")

    reply = parse_supervisor_reply(payload.text or payload.html)
    if not reply:
        raise HTTPException(400, "Empty reply")

    resolve_escalation(esc_id, reply)

    if conv_id:
        await broadcast(conv_id, {
            "type": "message",
            "role": "supervisor",
            "content": reply,
            "escalation_id": esc_id
        })

    return {"ok": True, "escalation_id": esc_id}


@app.get("/api/activities")
async def activities():
    from database import search_activities
    return search_activities()


@app.get("/api/escalations/pending")
async def escalations():
    return get_pending_escalations()


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
