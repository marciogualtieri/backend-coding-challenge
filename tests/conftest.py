import pytest
from aioresponses import aioresponses

from gistapi.gistapi import app as gistapi_app


@pytest.fixture()
def app():
    gistapi_app.config.update(
        {
            "TESTING": True,
        }
    )
    yield gistapi_app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def aioresponse_mock():
    with aioresponses() as m:
        yield m
