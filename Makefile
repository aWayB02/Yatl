check:
	poetry run ruff check . --fix

format:
	poetry run ruff format .

server:
	poetry run python src/yatl/base_api.py

run_yaml:
	poetry run python -m src.yatl.run

test:
	poetry run pytest