# AGENTS.md

Context for AI agents working on this repo. Read this first to avoid re-deriving the project.

## Project
Developer Voice Agent: an agentic voice assistant for developers, built in public, phase by phase.
Owner: Bishal Chakraborty (github: satyanweshi11).

## Roadmap
- Phase 1 (phase1-chat/): real-time WebSocket chat. [current]
- Phase 2: Claude streaming responses back over the same socket.
- Phase 3: voice (speech-to-text in, text-to-speech out).
- Phase 4: telephony / IVR (VoIP).

## Stack
- Python (version per pyproject.toml), FastAPI, uvicorn, websockets. Managed with uv.
- Frontend: vanilla HTML/JS, no build step.

## Run (phase1-chat)
    cd phase1-chat
    uv sync
    uv run uvicorn server:app --reload
Open http://127.0.0.1:8000

## Conventions
- Clean, idiomatic, self-documenting code. No explanatory comments.
- Async-first. Guard shared state with locks.
- Security at every boundary: validate and bound all client input, allowlist origins, rate-limit.
- No secrets in code. Config via environment variables.
- Small, focused commits: one feature per commit.

## Workflow
- One small feature per day, reviewed locally before push.
- Each feature ships with a short what/why note for the owner's study (kept out of the code).
