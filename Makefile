.PHONY: up build bootstrap lint down

## Start the full stack (builds all images first)
up:
	docker-compose up --build

## Build all Docker images without starting
build:
	docker-compose build

## Bootstrap component repositories as submodules (or use --method=clone)
bootstrap:
	bash ./scripts/bootstrap_submodules.sh --method=submodule

## Run linters across gateway and any other local services
lint:
	@echo ">>> Linting gateway (Python)..."
	@cd gateway && pip install flake8 --quiet && flake8 . --max-line-length=120 || true
	@echo ">>> Linting desktop/electron (JS)..."
	@cd desktop/electron && npx eslint . --ext .js || true

## Stop and remove containers
down:
	docker-compose down
