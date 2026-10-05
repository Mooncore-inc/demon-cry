.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

.PHONY: setup
setup: ## Install dependencies and configure the environment
	uv sync --all-groups
	uv run pre-commit install

.PHONY: test
test: ## Run the test suite
	uv run pytest

.PHONY: lint
lint: lint-ruff lint-ty lint-typos ## Run all linters (ruff + ty + typos)

.PHONY: lint-ruff
lint-ruff: ## Run ruff linter
	uv run ruff check .

.PHONY: lint-ty
lint-ty: ## Run type checker
	uv run ty check

.PHONY: lint-typos
lint-typos: ## Check spelling
	uv run typos

.PHONY: lint-fix
lint-fix: ## Run linters and auto-fix issues
	uv run ruff check --fix .

.PHONY: format
format: ## Format code automatically
	uv run ruff format
