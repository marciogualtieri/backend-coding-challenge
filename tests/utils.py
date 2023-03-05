import hashlib
from typing import Any, List

from aioresponses.core import aioresponses
from requests_mock.mocker import Mocker


def fake_gist_id(username: str, filenames: List[str]) -> str:
    """
    Generates a fake ID for the Gist (only unique to the username and Gist's filenames).
    """
    return hashlib.md5((username + str(sorted(filenames))).encode()).hexdigest()


def fake_gist(username: str, filenames: List[str]) -> dict[str, Any]:
    """
    Generates a fake Gist for testing based on the latest schema for the Gist API.
    """
    gist_id = fake_gist_id(username, filenames)

    files = {
        filename: {
            "filename": filename,
            "type": "text/plain",
            "language": "Text",
            f"raw_url": f"https://gist.githubusercontent.com/{username}/{gist_id}/raw/{hashlib.md5(filename.encode()).hexdigest()}/{filename}",
            "size": 75,
        }
        for filename in filenames
    }

    return {
        "url": f"https://api.github.com/gists/{gist_id}",
        "forks_url": f"https://api.github.com/gists/{gist_id}/forks",
        "commits_url": f"https://api.github.com/gists/{gist_id}/commits",
        "id": gist_id,
        "node_id": "G_kwDOACkMq9oAIDQ4ZjdmMGFlNDQwOWQwOWE3MDM2MThkZDkyNjVhZDg3",
        "git_pull_url": f"https://gist.github.com/{gist_id}.git",
        "git_push_url": f"https://gist.github.com/{gist_id}.git",
        "html_url": f"https://gist.github.com/{gist_id}",
        "files": files,
        "public": True,
        "created_at": "2023-03-03T12:54:32Z",
        "updated_at": "2023-03-03T12:54:32Z",
        "description": "",
        "comments": 0,
        "user": "None",
        "comments_url": f"https://api.github.com/gists/{gist_id}/comments",
        "owner": {
            "login": "{username}",
            "id": 2690219,
            "node_id": "MDQ6VXNlcjI2OTAyMTk=",
            "avatar_url": "https://avatars.githubusercontent.com/u/2690219?v=4",
            "gravatar_id": "",
            "url": f"https://api.github.com/users/{username}",
            "html_url": f"https://github.com/{username}",
            "followers_url": f"https://api.github.com/users/{username}/followers",
            "following_url": f"https://api.github.com/users/{username}/following{{/other_user}}",
            "gists_url": f"https://api.github.com/users/{username}/gists{{/gist_id}}",
            "starred_url": f"https://api.github.com/users/{username}/starred{{/owner}}{{/repo}}",
            "subscriptions_url": f"https://api.github.com/users/{username}/subscriptions",
            "organizations_url": f"https://api.github.com/users/{username}/orgs",
            "repos_url": f"https://api.github.com/users/{username}/repos",
            "events_url": f"https://api.github.com/users/{username}/events{{/privacy}}",
            "received_events_url": f"https://api.github.com/users/{username}/received_events",
            "type": "User",
            "site_admin": False,
        },
        "truncated": False,
    }


def mock_gist_files_requests(
    aioresponse_mock: aioresponses,
    username: str,
    files: dict[str, str],
) -> None:
    """
    Mocks the Gist API's response for a call to retrieve each one of the gist files.
    """
    gist_id = fake_gist_id(username, list(files.keys()))

    for filename, text in files.items():
        file_id = hashlib.md5(filename.encode()).hexdigest()
        url = f"https://gist.githubusercontent.com/{username}/{gist_id}/raw/{file_id}/{filename}"
        aioresponse_mock.get(
            url,
            status=200,
            body=text,
        )


def mock_gist_request(
    requests_mock: Mocker, username: str, gists: List[dict[str, Any]], per_page: int = 1
) -> None:
    """
    Mocks the Gist API's response for a call to retrieve gists for a particular user.
    """

    page = 1
    for i in range(0, len(gists), per_page):
        requests_mock.get(
            f"https://api.github.com/users/{username}/gists?page={page}",
            json=gists[i : i + per_page],
        )
        page += 1
    requests_mock.get(
        f"https://api.github.com/users/{username}/gists?page={page}", json=[]
    )
