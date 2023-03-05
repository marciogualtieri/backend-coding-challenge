"""
Exposes a simple HTTP API to search a users Gists via a regular expression.

Github provides the Gist service as a pastebin analog for sharing code and
other develpment artifacts.  See http://gist.github.com for details.  This
module implements a Flask server exposing two endpoints: a simple ping
endpoint to verify the server is up and responding and a search endpoint
providing a search across all public Gists for a given Github account.
"""

import asyncio
import re
from asyncio.locks import Semaphore
from http import HTTPStatus
from typing import Any, List

import aiohttp
import requests
from aiohttp.client import ClientSession
from flask import Flask, Response, jsonify, make_response, request
from flask.typing import ErrorHandlerCallable, ResponseReturnValue
from flask_expects_json import expects_json
from werkzeug.exceptions import BadRequest

SEARCH_POST_DATA_SCHEMA = {
    "type": "object",
    "properties": {"username": {"type": "string"}, "pattern": {"type": "string"}},
    "required": ["username", "pattern"],
    "additionalProperties": False,
}


class PatternFound(Exception):
    """
    Special exception to be raised when a gist with the pattern is found.
    We abort all asyncio tasks when one of them finds a gist file containing the pattern.
    """


class GitHubError(Exception):
    """
    Special exception to be raised when a GitHub API responds with an error.
    """

    def __init__(self, status_code: int, payload: dict[str, Any]):
        self.status_code = status_code
        self.payload = payload
        super().__init__()


app = Flask(__name__)


@app.errorhandler(400)
def bad_request(error: BadRequest) -> BadRequest | ResponseReturnValue:
    """
    Handles validations, return JSON response on errors.
    """
    original_error = error.description
    return make_response(jsonify({"error": original_error.message}), 400)


@app.errorhandler(Exception)
def exception_handler(
    error: ErrorHandlerCallable,
) -> ErrorHandlerCallable | ResponseReturnValue:
    """
    Handles validations, return JSON response on errors.
    """

    if isinstance(error, GitHubError):
        app.logger.error("GitHub API error: %s (%s)", error.payload, error.status_code)
        return make_response(
            jsonify({"error": "Internal error. Please contact technical support."}), 500
        )

    if isinstance(error, re.error):
        return make_response(jsonify({"error": f"Invalid pattern, {str(error)}"}), 400)

    return make_response(
        jsonify({"error": "Internal error. Please contact technical support."}), 500
    )


@app.route("/ping")
def ping() -> str:
    """Provide a static response to a simple GET request."""
    return "pong"


def gists_for_user(username: str) -> List[dict[str, Any]]:
    """Provides the list of gist metadata for a given user.

    This abstracts the /users/:username/gist endpoint from the Github API.
    See https://developer.github.com/v3/gists/#list-a-users-gists for
    more information.

    The original version didn't take into account pagination, that is, if the user had more than 30 gists,
    only the first page (30 gists) would be returned (page=1 and per_page=30 by default).
    It's important to note that the Gists API returns at most 3K gists.

    Args:
        username (string): the user to query gists for

    Returns:
        The dict parsed from the json response from the Github API.  See
        the above URL for details of the expected structure.
    """
    gists_url = "https://api.github.com/users/{username}/gists".format(
        username=username
    )
    page = 1
    gists = []
    data = []

    while True:
        response = requests.get(gists_url, params={"page": page})

        # Error responses from the GitHub API are forwared by this API's
        if response.status_code != HTTPStatus.OK:
            raise GitHubError(response.status_code, response.json())

        data = response.json()

        # Empty page means that there are no more pages to fetch
        if not data:
            break

        gists += data
        page += 1

    return gists


async def check_file_contains_pattern(
    file_url: str,
    pattern: re.Pattern[str],
    semaphore: Semaphore,
    session: ClientSession,
) -> None:
    """
    Checks if gist file contains the input pattern, throws an exception if that's the case.
    """

    async with semaphore, session.get(file_url) as response:
        if response.status == HTTPStatus.OK:
            content = await response.text()
            if pattern.match(content) is not None:
                raise PatternFound()
        else:
            data = await response.json()
            raise GitHubError(response.status, data)


async def gist_contains_pattern(gist: dict[str, Any], pattern: re.Pattern[str]) -> bool:
    """
    Test if any of the files for the gist contains the input pattern using asynchronous tasks.
    """

    files_urls = [file["raw_url"] for file in gist["files"].values()]

    semaphore = asyncio.Semaphore(len(files_urls))

    async with aiohttp.ClientSession() as session:
        tasks = []
        for file_url in files_urls:
            tasks.append(
                asyncio.create_task(
                    check_file_contains_pattern(file_url, pattern, semaphore, session)
                )
            )

        try:
            await asyncio.gather(*tasks)
        except PatternFound:
            return True

    return False


def gist_contains_pattern_sync(gist: dict[str, Any], pattern: re.Pattern[str]) -> bool:
    """
    Executes gist_contains_pattern (an async function), synchronosly.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    found = loop.run_until_complete(gist_contains_pattern(gist, pattern))
    loop.close()

    return found


@app.route("/api/v1/search", methods=["POST"])
@expects_json(SEARCH_POST_DATA_SCHEMA)
def search() -> Response:
    """Provides matches for a single pattern across a single users gists.

    Pulls down a list of all gists for a given user and then searches
    each gist for a given regular expression.

    Returns:
        A Flask Response object of type application/json.  The result
        object contains the list of matches along with a 'status' key
        indicating any failure conditions.
    """
    post_data = request.get_json()

    username = post_data["username"]
    pattern = post_data["pattern"]

    result: dict[str, Any] = {}
    gists = gists_for_user(username)

    matches: List[str] = []
    for gist in gists:
        # Fetchs each gist and check for the pattern
        if gist_contains_pattern_sync(gist, re.compile(pattern, re.S)):
            matches.append(gist["url"])

    result["status"] = "success"
    result["username"] = username
    result["pattern"] = pattern
    result["matches"] = matches

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=9876)
