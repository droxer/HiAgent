.PHONY: backend web dev install install-backend install-web clean

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

# Production build
build-web:
	cd web && npm run build

# Clean generated files
clean:
	rm -rf backend/.venv web/node_modules web/.next
