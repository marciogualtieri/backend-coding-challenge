# Developer's Guide

## Gists API

For reference, you can find more information about the listing public gists [here](https://docs.github.com/en/rest/gists/gists?apiVersion=2022-11-28#list-public-gists).

Note that the listing end-point is paginated, that is, you may provide a page index (`page`, starting from 1) and page size (`per_page`).

## Setting Up a Development Environment

Configure the virtual environment's location:

```commandLine
poetry config virtualenvs.in-project true
```

Create the virtual environment:

```commandLine
poetry install
```

Activate the virtual environment:

```commandLine
source .venv/bin/activate
```

## Running Tests

```commandLine
pytest -s -v
```

You may also change the logging level:

```commandLine
pytest -s -v --log-cli-level=DEBUG
```

You should get an output similar to this:

```commandLine
============================================ test session starts =====================================================================
platform linux -- Python 3.10.9, pytest-7.2.1, pluggy-1.0.0 -- /home/franco/workspace/locoia/backend-coding-challenge/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/franco/workspace/locoia/backend-coding-challenge
plugins: requests-mock-1.10.0, cov-4.0.0
collected 9 items                                                                                                                                                                                          

tests/test_ping.py::test__ping__ok PASSED
tests/test_search.py::test__search__missing_post_data PASSED
tests/test_search.py::test__search__invalid_post_data PASSED
tests/test_search.py::test__search__github_api_error_listing_user_gists PASSED
tests/test_search.py::test__search__github_api_error_fetching_gist_files PASSED
tests/test_search.py::test__search__invalid_pattern PASSED
tests/test_search.py::test__search__single_page_found PASSED
tests/test_search.py::test__search__single_page_not_found PASSED
tests/test_search.py::test__search__multiple_pages_found PASSED

============================================= 9 passed in 0.08s ======================================================================
```

## Running the App in Development Mode

Start the service:

```commandLine
flask --app gistapi.gistapi run --debugger
```

Send some requests:

```commandLine
curl \
  --header "Content-Type: application/json" \
  --request POST \
  --data '{"username":"justdionysus","pattern":".*import requests.*"}' \
  http://127.0.0.1:5000/api/v1/search
```

### Coverage Reports

You also can produce coverage reports:

```commandline
pytest --cov=. --cov-report=html
```

Results will be available inside the folder [./htmlconv](./htmlconv).

You should see an output similar to the following:

```commandLine
============================================ test session starts ============================================
platform linux -- Python 3.10.9, pytest-7.2.1, pluggy-1.0.0
rootdir: /home/franco/workspace/locoia/backend-coding-challenge
plugins: requests-mock-1.10.0, cov-4.0.0
collected 9 items                                                                                                                                                                                          

tests/test_ping.py .                                                                                   [ 11%]
tests/test_search.py ........                                                                          [100%]

---------- coverage: platform linux, python 3.10.9-final-0 -----------
Coverage HTML written to dir htmlcov

============================================== 9 passed in 0.15s =============================================
```



### Formatting and Linting

Formatting is performed using [black](https://github.com/psf/black), [isort](https://pycqa.github.io/isort/), and [autoflake](https://github.com/PyCQA/autoflake).

Typing is checked using [mypy](https://mypy-lang.org/).

Configuration for these can be found in the file [./pyproject.toml](./pyproject.toml).

You may perform a full check using the following command:

```commandLine
black --check . && isort --check-only . && mypy .
```

You may also use the Honcho shortcuts describe in the next section.

### Custom Honcho Commands

Shortcuts to all commands used in this project are available through [Honcho](https://honcho.readthedocs.io/en/latest/).

| Command       | Description                                                                                                      |
|---------------|------------------------------------------------------------------------------------------------------------------|
| service       | Runs service using [Gunicorn](https://gunicorn.org/) (meant to be used by the Docker image).                     |
| format        | Formats code.                                                                                                    |
| check         | Checks formatting and typing (meant to be used by CI/CD pipelines).                                              |
| test          | Runs all tests.                                                                                                  |
| coverage      | Generates coverage reports.                                                                                      |
| runserver     | Runs the service in development mode.                                                                            |


Simply run `honcho start <command>` to perform the command, e.g., the perform code formatting:

```commandLine
honcho start format
```

## Running the App with Docker

You may run the application using docker, without setting up a development environment:

```commandLine
docker build . -t gistapi-service
docker run --name gistapi-service -p 127.0.0.1:5000:5000/tcp -t gistapi-service
```

You may stop the service by running the following command:

```commandLine
docker stop gistapi-service
docker rm gistapi-service
```

The application will be available to your browser via this URL: [http://localhost:5000/](http://localhost:5000/).
