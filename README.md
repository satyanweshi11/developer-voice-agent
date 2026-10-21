# Developer Voice Agent

A build-in-public project: an agentic voice assistant for developers, grown in
phases from a real-time chat into a full voice + telephony agent.

## Phases
- **Phase 1 — Real-time WebSocket chat** ✅ FastAPI WebSocket server with a
  concurrency-safe connection manager and a minimal browser client.
- **Phase 2 — Claude in the loop** (next) stream an agent's responses back over
  the same socket.
- **Phase 3 — Voice** speech-to-text in, text-to-speech out.
- **Phase 4 — Telephony / IVR** VoIP + IVR: a real "Claude phone."

## Phase 1 — run it
```bash
cd phase1-chat
uv sync
uv run uvicorn server:app --reload
```
Then open http://127.0.0.1:8000

### What's inside
- `server.py` — FastAPI app with a `/ws` WebSocket endpoint and a
  concurrency-safe `ConnectionManager` (asyncio.Lock, resilient broadcast that
  prunes dead clients).
- `index.html` — vanilla-JS client (auto `ws`/`wss`, XSS-safe rendering).

---
Built by **Bishal Chakraborty** — [LinkedIn](https://linkedin.com/in/chakraborty11bishal)
