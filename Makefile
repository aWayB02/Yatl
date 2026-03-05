check:
	poetry run ruff check . --fix

format:
	poetry run ruff format .

make run:
	poetry run python src/yatl/test_server.py