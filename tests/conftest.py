import os
from functools import partial
from typing import Any, Callable, Generator

import pytest
import requests

from tests.helpers import utils
from tests.helpers.api_client import ApiClient


@pytest.fixture(scope="session")
def api_client() -> Generator[ApiClient, None, None]:
    with requests.Session() as session:
        session.trust_env = False
        base_url = os.environ.get("BASE_URL", "http://localhost:3000")
        environment = os.environ.get("TARGET_ENV", "dev")
        token = os.getenv("API_TOKEN", "mysecrettoken")
        yield ApiClient(session, base_url, environment, token)


@pytest.fixture(scope="session")
def api_schema() -> dict[str, Any]:
    return utils.load_schema()


@pytest.fixture(scope="session")
def get_api_schema(
    api_schema: dict[str, Any],
) -> Callable[[str, str, int], dict[str, Any]]:
    return partial(utils.extract_schema, api_schema)


@pytest.fixture
def validate_response_schema() -> Callable[[requests.Response, dict[str, Any]], None]:
    return utils.validate_response_schema


@pytest.fixture
def make_user_payload():
    return utils.make_user_payload


@pytest.fixture
def user_path() -> Callable[[str | int], str]:
    return utils.user_path


@pytest.fixture
def register_user_cleanup(
    request: pytest.FixtureRequest,
) -> Callable[[ApiClient, str | int], None]:
    def register(api_client: ApiClient, email: str | int) -> None:
        cleanup_email = str(int(email)) if isinstance(email, bool) else str(email)
        request.addfinalizer(partial(utils.delete_test_user, api_client, cleanup_email))

    return register


@pytest.fixture
def create_user_with_cleanup(
    register_user_cleanup,
) -> Callable[[ApiClient, dict[str, Any]], requests.Response]:
    def create(api_client: ApiClient, payload: dict[str, Any]) -> requests.Response:
        response = api_client.create_user(payload)
        if response.status_code == 201:
            email = payload.get("email")
            if isinstance(email, (str, int)):
                register_user_cleanup(api_client, email)
        return response

    return create


@pytest.fixture
def create_prerequisite_user(
    register_user_cleanup,
) -> Callable[[ApiClient, dict[str, Any]], dict[str, Any]]:
    def create_user(api_client: ApiClient, payload: dict[str, Any]) -> dict[str, Any]:
        user_payload = utils.make_user_payload(**payload)
        # Register before creation so failed response checks still trigger cleanup.
        register_user_cleanup(api_client, user_payload["email"])
        return utils.create_unique_user(api_client, user_payload)

    return create_user
