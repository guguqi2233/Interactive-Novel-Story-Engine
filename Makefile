.PHONY: install dev backend frontend docker-up docker-down test build

install:
	cd backend && python -m pip install -r requirements.txt
	cd frontend && npm install

dev:
	@echo "Start backend and frontend in separate terminals:"
	@echo "  make backend"
	@echo "  make frontend"

backend:
	cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8010

frontend:
	cd frontend && npm run dev

docker-up:
	docker compose up --build

docker-down:
	docker compose down

test:
	python -m pytest backend
	cd frontend && npm run typecheck

build:
	cd frontend && npm run build
