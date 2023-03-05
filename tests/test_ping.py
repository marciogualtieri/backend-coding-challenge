from http import HTTPStatus

from flask.testing import FlaskClient


def test__ping__ok(client: FlaskClient) -> None:
    response = client.get("/ping")
    assert response.status_code == HTTPStatus.OK
    assert b"pong" in response.data
