.PHONY: backend web dev install install-backend install-web build-web build-sandbox push-sandbox migrate clean

# Start both backend and web concurrently
dev: install
	@echo "Starting backend and web..."
	$(MAKE) -j2 backend web

# Backend (FastAPI + uvicorn)
backend:
	cd backend && uv run python -m api.main

# Web (Vite dev server)
web:
	cd web && npm run dev

# Install all dependencies
install: install-backend install-web

install-backend:
	cd backend && uv sync

install-web:
	cd web && npm install

# Database migrations
migrate:
	cd backend && uv run alembic upgrade head

# Production build
build-web:
	cd web && npm run build

# Build sandbox Docker images (from container/ folder)
build-sandbox:
	docker build -t ghcr.io/droxer/hiagent-sandbox-default -f container/Dockerfile.default container
	docker build -t ghcr.io/droxer/hiagent-sandbox-data-science -f container/Dockerfile.data_science container
	docker build -t ghcr.io/droxer/hiagent-sandbox-browser -f container/Dockerfile.browser container

# Push sandbox Docker images to GHCR
push-sandbox:
	docker push ghcr.io/droxer/hiagent-sandbox-default
	docker push ghcr.io/droxer/hiagent-sandbox-data-science
	docker push ghcr.io/droxer/hiagent-sandbox-browser

# Clean generated files
clean:
	rm -rf backend/.venv web/node_modules web/.next
