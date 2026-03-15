# HiAgent

A full-stack AI agent framework with a Python/FastAPI backend and TypeScript/Next.js frontend, connected via Server-Sent Events (SSE).

Users assign tasks through a chat interface. The backend runs a ReAct loop — reasoning, planning, and executing tools in a sandboxed environment — while the frontend streams progress in real time.

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js (with npm)
- [`uv`](https://docs.astral.sh/uv/) package manager

### Setup

```bash
# Clone and install all dependencies
make install

# Create backend/.env with required keys (see backend/.env.example)
# ANTHROPIC_API_KEY=...
# TAVILY_API_KEY=...

# Start backend (port 8000) + frontend (port 3000)
make dev
```

Open [http://localhost:3000](http://localhost:3000).

## Commands

```bash
make dev              # Start backend + frontend concurrently
make backend          # Backend only (port 8000)
make web              # Frontend only (port 3000)
make install          # Install all dependencies
make build-web        # Production frontend build
make clean            # Remove .venv, node_modules, .next
```

### Backend Testing & Linting

Run from `backend/`:

```bash
uv run pytest                          # All tests
uv run pytest path/to/test.py::test_fn # Single test
uv run pytest --cov                    # With coverage
uv run ruff check .                    # Lint
uv run ruff format .                   # Format
```

## Architecture

```
HiAgent/
├── backend/
│   ├── api/              # FastAPI endpoints + SSE event emitter
│   ├── agent/
│   │   ├── loop/         # ReAct orchestrator, planner, sub-agent manager
│   │   ├── llm/          # Claude API client (anthropic SDK)
│   │   ├── tools/        # Tool registry, executor, built-in tools
│   │   ├── sandbox/      # Execution sandbox providers (E2B, BoxLite)
│   │   └── skills/       # YAML skill definitions
│   └── config/           # Pydantic Settings
├── web/
│   ├── src/
│   │   ├── app/          # Next.js App Router
│   │   ├── features/     # Feature modules (welcome, task-view, conversation, agent-activity)
│   │   ├── shared/       # Shared components, hooks, types, stores
│   │   └── hooks/        # SSE + agent state hooks
│   └── next.config.ts    # API proxy to backend
└── Makefile
```

### Data Flow

1. User sends a message → frontend POSTs to `/api/tasks`
2. Frontend opens SSE connection to `/api/tasks/{taskId}/events`
3. Backend runs the ReAct loop: LLM call → tool execution → emit events → repeat
4. Frontend renders events in real time across chat and activity panels

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/tasks` | Create a new task |
| `GET` | `/tasks/{task_id}/events` | SSE stream of agent events |
| `POST` | `/tasks/{task_id}/respond` | Submit user response to agent prompt |

## Tech Stack

**Backend:** Python 3.12+, FastAPI, Anthropic SDK, Pydantic, uv

**Frontend:** Next.js 15 (App Router, Turbopack), React 19, Tailwind CSS 4, Zustand, Framer Motion

## Environment Variables

Required in `backend/.env`:

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key for Claude |
| `TAVILY_API_KEY` | Yes | Tavily API key for web search |
| `REDIS_URL` | No | Redis URL for state persistence |

## License

Private
