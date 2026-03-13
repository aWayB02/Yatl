check:
	poetry run ruff check . --fix

format:
	poetry run ruff format .

server:
	poetry run python src/yatl/base_api.py

test_ya:
	poetry run python -m src.yatl.run

test:
	poetry run pytest