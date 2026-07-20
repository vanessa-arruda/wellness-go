.PHONY: install-hooks lint format format-check test check

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

check: lint format-check test
