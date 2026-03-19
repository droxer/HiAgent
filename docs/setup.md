**English** | [简体中文](zh-CN/setup.md)

# Local Setup Guide

Step-by-step instructions to get HiAgent running on your machine.

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.12+ | [python.org](https://www.python.org/downloads/) |
| Node.js | 18+ (with npm) | [nodejs.org](https://nodejs.org/) |
| uv | latest | [docs.astral.sh/uv](https://docs.astral.sh/uv/) |
| PostgreSQL | 14+ (optional) | [postgresql.org](https://www.postgresql.org/download/) |
| Docker | latest (optional) | [docker.com](https://www.docker.com/get-started/) |

> **PostgreSQL** is optional — without it, conversations are not persisted across server restarts.
> **Docker** is only needed if you want sandboxed code execution via Boxlite.

### Verify Prerequisites

```bash
python3 --version   # 3.12+
node --version       # 18+
uv --version         # any recent version
```

---

## 1. Clone the Repository

```bash
git clone https://github.com/droxer/HiAgent.git
cd HiAgent
```

---

## 2. Install Dependencies

```bash
make install
```

This runs `uv sync` for the backend and `npm install` for the frontend.

To install them separately:

```bash
make install-backend   # cd backend && uv sync
make install-web       # cd web && npm install
```

---

## 3. Configure Environment Variables

Copy the example file and fill in your API keys:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:

```bash
# Required — you must set these
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=tvly-...

# Optional — sandbox provider (default: boxlite)
SANDBOX_PROVIDER=local          # Use "local" for development without Docker

# Optional — database (remove or leave empty to skip persistence)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/hiagent
```

### API Keys

| Key | Where to get it | Required |
|-----|----------------|----------|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com/) | Yes |
| `TAVILY_API_KEY` | [tavily.com](https://tavily.com/) | Yes |
| `MINIMAX_API_KEY` | [minimaxi.com](https://www.minimaxi.com/) | No (enables image generation) |
| `E2B_API_KEY` | [e2b.dev](https://e2b.dev/) | No (only if `SANDBOX_PROVIDER=e2b`) |

### Sandbox Providers

| Provider | When to use | Requires |
|----------|------------|----------|
| `local` | Development — runs code as local subprocesses (no isolation) | Nothing |
| `boxlite` | Production — isolated micro-VMs | Docker |
| `e2b` | Cloud sandboxes | `E2B_API_KEY` |

For local development, set `SANDBOX_PROVIDER=local` to skip Docker entirely.

---

## 4. Set Up the Database (Optional)

If you want conversation persistence, create a PostgreSQL database:

```bash
createdb hiagent
```

Make sure `DATABASE_URL` in `backend/.env` points to it:

```
DATABASE_URL=postgresql+asyncpg://localhost:5432/hiagent
```

Then run migrations:

```bash
cd backend && uv run alembic upgrade head
```

> Skip this step if you don't need persistence. The app works without a database.

---

## 5. Start the Dev Server

```bash
make dev
```

This starts both services concurrently:
- **Backend** (FastAPI): http://localhost:8000
- **Frontend** (Next.js): http://localhost:3000

Open http://localhost:3000 in your browser.

To run them separately (useful for debugging):

```bash
# Terminal 1
make backend    # cd backend && uv run python -m api.main

# Terminal 2
make web        # cd web && npm run dev
```

---

## 6. Build Sandbox Images (Optional)

If using `SANDBOX_PROVIDER=boxlite`, build the Docker images:

```bash
make build-sandbox
```

This builds three images:
- `hiagent-sandbox-default` — Python, Node.js, git
- `hiagent-sandbox-data-science` — pandas, numpy, matplotlib
- `hiagent-sandbox-browser` — Playwright + Chromium

---

## Project Structure

```
HiAgent/
├── backend/           # Python/FastAPI backend
│   ├── api/           # Routes, middleware, app factory
│   ├── agent/         # Agent runtime, tools, sandbox, skills
│   ├── config/        # Settings (Pydantic)
│   ├── migrations/    # Alembic database migrations
│   └── tests/         # pytest test suite
├── web/               # Next.js frontend
│   └── src/
│       ├── app/       # Pages (App Router)
│       ├── features/  # Feature modules (conversation, agent-computer, skills, mcp)
│       ├── shared/    # Shared components, hooks, stores, types
│       └── i18n/      # Internationalization (en, zh-CN)
├── container/         # Sandbox Dockerfiles
├── docs/              # Documentation
└── Makefile           # Dev commands
```

---

## Common Commands

| Command | Description |
|---------|-------------|
| `make dev` | Start backend + frontend |
| `make backend` | Start backend only |
| `make web` | Start frontend only |
| `make install` | Install all dependencies |
| `make build-web` | Production build of frontend |
| `make build-sandbox` | Build sandbox Docker images |
| `make migrate` | Run database migrations |
| `make clean` | Remove `.venv`, `node_modules`, `.next` |

### Backend Testing & Linting

Run from the `backend/` directory:

```bash
uv run pytest                          # Run all tests
uv run pytest path/to/test.py::test_fn # Run a single test
uv run pytest --cov                    # With coverage report
uv run ruff check .                    # Lint
uv run ruff format .                   # Auto-format
```

---

## Troubleshooting

### Port already in use

```bash
# Find and kill the process on port 8000 or 3000
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

### `uv` not found

Install uv:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Database connection refused

- Check PostgreSQL is running: `pg_isready`
- Verify `DATABASE_URL` in `backend/.env` matches your local setup
- If you don't need persistence, remove or comment out `DATABASE_URL`

### Sandbox errors with `boxlite`

- Make sure Docker is running: `docker info`
- Build images first: `make build-sandbox`
- Or switch to `SANDBOX_PROVIDER=local` for development

### Frontend can't reach backend

The frontend proxies `/api/*` requests to `http://127.0.0.1:8000`. Make sure the backend is running on port 8000. If you changed the backend port, update `web/next.config.ts`.

---

## Next Steps

- [Development Guide](development.md) — Architecture deep-dive, API reference, environment variables
- [Design Style Guide](DESIGN_STYLE_GUIDE.md) — UI patterns, color system, typography
- [Brand Guidelines](brand-guidelines.md) — Brand identity and visual language
