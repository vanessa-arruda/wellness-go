.PHONY: install-hooks lint format format-check test check \
	frontend-lint frontend-typecheck frontend-format frontend-format-check frontend-build frontend-check

install-hooks:
	git config core.hooksPath .githooks
	@echo "Git hooks installed (commit-msg format check, pre-commit lint/format check)."

lint:
	cd backend && .venv/bin/ruff check .

format:
	cd backend && .venv/bin/ruff format .

format-check:
	cd backend && .venv/bin/ruff format --check .

test:
	cd backend && .venv/bin/python -m pytest

check: lint format-check test frontend-check

frontend-lint:
	cd frontend && npm run lint

frontend-typecheck:
	cd frontend && npm run typecheck

frontend-format:
	cd frontend && npm run format

frontend-format-check:
	cd frontend && npm run format:check

frontend-build:
	cd frontend && npm run build

frontend-check: frontend-lint frontend-typecheck frontend-format-check frontend-build
