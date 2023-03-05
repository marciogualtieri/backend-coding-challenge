import hashlib
import json
from http import HTTPStatus
from unittest import mock

from aioresponses.core import aioresponses
from flask.testing import FlaskClient
from requests_mock.mocker import Mocker

from gistapi.gistapi import app as gistapi_app
from tests import utils as test_helpers

TEST_USERNAME = "testuser"

SEARCH_URL = "/api/v1/search"

TEST_GIST_FILES = [
    (
        "file1.txt",
        """
        Do what you can, with what you have, where you are. 
          - Theodore Roosevelt
        """,
    ),
    (
        "file2.txt",
        """
        Where's the beef? 
          - Clara Peller
        """,
    ),
    (
        "file3.txt",
        """
        Perfect is the enemy of good.
          - Voltaire
        """,
    ),
]


def test__search__missing_post_data(client: FlaskClient) -> None:
    response = client.post(
        SEARCH_URL,
        json={"pattern": "pattern"},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    data = json.loads(response.data)
    assert data == {"error": "'username' is a required property"}


def test__search__invalid_post_data(client: FlaskClient) -> None:
    response = client.post(
        SEARCH_URL,
        json={
            "username": TEST_USERNAME,
            "pattern": "pattern",
            "invalid": "attribute",
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    data = json.loads(response.data)
    assert data == {
        "error": "Additional properties are not allowed ('invalid' was unexpected)"
    }


def test__search__github_api_error_listing_user_gists(
    client: FlaskClient, requests_mock: Mocker
) -> None:
    error_status_code = 403
    error_payload = {"some": "error"}

    requests_mock.get(
        f"https://api.github.com/users/{TEST_USERNAME}/gists?page=1",
        json=error_payload,
        status_code=error_status_code,
    )

    with mock.patch.object(gistapi_app.logger, "error") as mock_logger_error:
        response = client.post(
            SEARCH_URL,
            json={"username": TEST_USERNAME, "pattern": ".*Theodore Roosevelt.*"},
        )

        assert response.status_code == 500
        data = json.loads(response.data)
        assert data == {"error": "Internal error. Please contact technical support."}

        mock_logger_error.assert_called_once_with(
            "GitHub API error: %s (%s)", error_payload, error_status_code
        )


def test__search__github_api_error_fetching_gist_files(
    client: FlaskClient, requests_mock: Mocker, aioresponse_mock: aioresponses
) -> None:
    error_status_code = 403
    error_payload = {"error": "Rate limit exceeded"}

    filename = TEST_GIST_FILES[0][0]
    gist = test_helpers.fake_gist(TEST_USERNAME, [filename])

    test_helpers.mock_gist_request(requests_mock, TEST_USERNAME, [gist])

    gist_id = gist["id"]
    file_id = hashlib.md5(filename.encode()).hexdigest()
    file_url = f"https://gist.githubusercontent.com/{TEST_USERNAME}/{gist_id}/raw/{file_id}/{filename}"
    aioresponse_mock.get(
        file_url,
        status=error_status_code,
        payload=error_payload,
    )

    with mock.patch.object(gistapi_app.logger, "error") as mock_logger_error:
        response = client.post(
            SEARCH_URL,
            json={"username": TEST_USERNAME, "pattern": ".*Theodore Roosevelt.*"},
        )

        assert response.status_code == 500
        data = json.loads(response.data)
        assert data == {"error": "Internal error. Please contact technical support."}

        mock_logger_error.assert_called_once_with(
            "GitHub API error: %s (%s)", error_payload, error_status_code
        )


def test__search__invalid_pattern(
    client: FlaskClient, requests_mock: Mocker, aioresponse_mock: aioresponses
) -> None:
    gist_files = dict(TEST_GIST_FILES)
    gist = test_helpers.fake_gist(TEST_USERNAME, list(gist_files.keys()))

    test_helpers.mock_gist_request(requests_mock, TEST_USERNAME, [gist])
    test_helpers.mock_gist_files_requests(aioresponse_mock, TEST_USERNAME, gist_files)

    response = client.post(
        SEARCH_URL,
        json={"username": TEST_USERNAME, "pattern": "["},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    data = json.loads(response.data)
    assert data == {
        "error": "Invalid pattern, unterminated character set at position 0"
    }


def test__search__single_page_found(
    client: FlaskClient, requests_mock: Mocker, aioresponse_mock: aioresponses
) -> None:
    gist_files = dict(TEST_GIST_FILES)
    gist = test_helpers.fake_gist(TEST_USERNAME, list(gist_files.keys()))

    test_helpers.mock_gist_request(requests_mock, TEST_USERNAME, [gist])
    test_helpers.mock_gist_files_requests(aioresponse_mock, TEST_USERNAME, gist_files)

    response = client.post(
        SEARCH_URL,
        json={"username": TEST_USERNAME, "pattern": ".*Theodore Roosevelt.*"},
    )

    assert response.status_code == HTTPStatus.OK
    data = json.loads(response.data)
    assert data["matches"] == [gist["url"]]


def test__search__single_page_not_found(
    client: FlaskClient, requests_mock: Mocker, aioresponse_mock: aioresponses
) -> None:
    gist_files = dict(TEST_GIST_FILES[:2])
    gist = test_helpers.fake_gist(TEST_USERNAME, list(gist_files.keys()))

    test_helpers.mock_gist_request(requests_mock, TEST_USERNAME, [gist])
    test_helpers.mock_gist_files_requests(aioresponse_mock, TEST_USERNAME, gist_files)

    response = client.post(
        SEARCH_URL,
        json={"username": TEST_USERNAME, "pattern": ".*Voltaire.*"},
    )

    assert response.status_code == HTTPStatus.OK
    data = json.loads(response.data)
    assert data["matches"] == []


def test__search__multiple_pages_found(
    client: FlaskClient, requests_mock: Mocker, aioresponse_mock: aioresponses
) -> None:
    page1_gist_files = dict(TEST_GIST_FILES[:2])
    page1_gist = test_helpers.fake_gist(TEST_USERNAME, list(page1_gist_files.keys()))

    page2_gist_files = dict(TEST_GIST_FILES[2:])
    page2_gist = test_helpers.fake_gist(TEST_USERNAME, list(page2_gist_files.keys()))

    test_helpers.mock_gist_request(
        requests_mock, TEST_USERNAME, [page1_gist, page2_gist], per_page=1
    )
    test_helpers.mock_gist_files_requests(
        aioresponse_mock, TEST_USERNAME, page1_gist_files
    )
    test_helpers.mock_gist_files_requests(
        aioresponse_mock, TEST_USERNAME, page2_gist_files
    )

    response = client.post(
        SEARCH_URL,
        json={"username": TEST_USERNAME, "pattern": ".*Voltaire.*"},
    )

    assert response.status_code == HTTPStatus.OK
    data = json.loads(response.data)
    assert data["matches"] == [page2_gist["url"]]
