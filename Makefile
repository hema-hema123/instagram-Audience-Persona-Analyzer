.PHONY: bootstrap api demo test evaluate format

bootstrap:
	bash scripts/bootstrap.sh

api:
	bash scripts/run_api.sh

demo:
	bash scripts/demo.sh

test:
	python -m pytest tests/ -v

evaluate:
	python -c "from app.evaluation import evaluate_model; import json; r = evaluate_model(); print(json.dumps(r, indent=2))"

format:
	@echo "Add black/ruff if you want"
