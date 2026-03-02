
# Architecture — Allout Travel Assistant

## The basic idea

Three agents each with a specific job. A supervisor at the top that reads the user's message and decides which specialist to hand off to. The booking agent handles anything transactional like searching checking availability creating bookings and escalating. 

I went with Google ADK's `sub_agents` pattern.


---

## Backend

### ADK + FastAPI

Each incoming message goes through an async `run_agent()` function that creates or reuse an ADK session and runs the root agent. The runner streams events back tool calls, intermediate steps, final response  and I grab the last `is_final_response()` event.

Sessions are in-memory for now.

### Message aggregation

Users can send multiple short messages in a row before waiting for a response. And that would cause an issue as we might get disconnected 

The fix is a 2.5 second debounce as every incoming message gets appended to a buffer.

### Real-time responses (SSE)

Responses go back to the browser via Server-Sent Events rather than WebSockets. The communication is entirely one-way — server pushes to client — so SSE is the simpler choice.

Each conversation gets an `asyncio.Queue`. When the agent finishes, the response gets broadcast to all queues registered for that conversation ID. This also means multiple tabs work fine.

### Human-in-the-loop

When the booking agent can't fulfill a request, it calls `escalate_to_supervisor`. That saves an escalation record to the DB, sends an HTML email to the supervisor with the customer's message, and returns a reference number to the customer.

The email has two custom headers: `X-Escalation-ID` and `X-Conversation-ID`. When the supervisor replies, their email client preserves those headers. The inbound webhook at `/api/webhook/email` reads them, parses out the reply text (stripping the quoted original), updates the DB record, and broadcasts the supervisor's response back to the right conversation via SSE. It shows up as a distinct "supervisor" bubble in the chat.

For testing without real email, there's a `/api/supervisor/reply` endpoint that does the same broadcast directly. The floating 👔 button in the UI calls that.

### Database

SQLite. It's a demo — no reason to run a full database server. Activities and their variations are seeded from a JSON file on first startup. The schema has four tables: activities, variations, bookings, escalations.

One slightly annoying thing about SQLite: no native array type. Timings and group sizes are stored as JSON strings and parsed back out on read. Not ideal but straightforward.

---

## Frontend

Standard React + Vite setup. The chat UI is styled to look like WhatsApp — dark background, green outgoing bubbles, double ticks, animated typing indicator.

All the chat state lives in a `useChat` hook: SSE connection, message list, typing state. Components just call the hook and render. `App.jsx` is mostly layout.

---
