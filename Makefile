.PHONY: bootstrap api demo test format

bootstrap:
	bash scripts/bootstrap.sh

api:
	bash scripts/run_api.sh

demo:
	bash scripts/demo.sh

test:
	@echo "No tests yet"

format:
	@echo "Add black/ruff if you want"
