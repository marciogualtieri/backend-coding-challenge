service: gunicorn --bind 0.0.0.0:5000 gistapi.gistapi:app
format: autoflake -i -r --remove-all-unused-imports . && black . & isort .
check: black --check . && isort --check-only . && mypy .
test: pytest -s -v --log-cli-level=DEBUG
coverage: pytest --cov=gistapi --cov-report=html
runserver: flask --app gistapi.gistapi run --debugger
