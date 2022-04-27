import os
from unittest import mock

import pytest
from click.testing import CliRunner
from syntropy_sdk import models
from syntropy_sdk.rest import ApiException

from syntropycli import __main__ as ctl


@pytest.fixture
def login_mock():
    with mock.patch(
        "syntropy_sdk.utils.login_with_access_token",
        autospec=True,
        returns="JWT access token",
    ) as the_mock:
        yield the_mock


@pytest.fixture
def env_mock():
    with mock.patch.dict(
        os.environ, {"SYNTROPY_API_SERVER": "server", "SYNTROPY_API_TOKEN": "token"}
    ) as the_mock:
        yield the_mock


@pytest.fixture
def runner(env_mock):
    return CliRunner()


@pytest.fixture
def print_table_mock():
    with mock.patch(
        "syntropycli.__main__.print_table",
        autospec=True,
    ) as the_mock:
        yield the_mock


@pytest.fixture
def mock_index_api_key():
    with mock.patch.object(
        ctl.sdk.AuthApi,
        "v1_network_auth_api_keys_get",
        autospec=True,
        return_value=models.V1NetworkAuthApiKeysGetResponse(
            [
                models.V1AuthApiKey(
                    **{
                        "api_key_name": "skip",
                        "api_key_id": 123,
                        "api_key_created_at": "date",
                        "api_key_updated_at": "date",
                        "api_key_status": "status",
                        "api_key_description": "a description",
                        "api_key_valid_until": "a date",
                    }
                ),
                models.V1AuthApiKey(
                    **{
                        "api_key_name": "test",
                        "api_key_id": 321,
                        "api_key_created_at": "date",
                        "api_key_updated_at": "date",
                        "api_key_status": "status",
                        "api_key_description": "a description",
                        "api_key_valid_until": "a date",
                    }
                ),
            ]
        ),
    ) as index_mock:
        yield index_mock


@pytest.fixture
def mock_delete_api_key():
    with mock.patch.object(
        ctl.sdk.AuthApi, "v1_network_auth_api_keys_delete", autospec=True
    ) as the_mock:
        yield the_mock


@pytest.fixture
def with_pagination():
    with mock.patch.object(
        ctl.sdk.utils,
        "WithPagination",
        autospec=True,
        side_effect=lambda x: x,
    ) as the_mock:
        yield the_mock


@pytest.fixture
def mock_create_api_key():
    with mock.patch.object(
        ctl.sdk.AuthApi,
        "v1_network_auth_api_keys_create",
        autospec=True,
        return_value=models.V1AuthApiKeysCreateItem(
            api_key_name="skip",
            api_key_id=123,
            user_id=1,
            api_key_secret="secret",
            api_key_created_at="date",
            api_key_updated_at="date",
            api_key_description="a description",
            api_key_valid_until="a date",
        ),
    ) as the_mock:
        yield the_mock


@pytest.fixture
def mock_agents_get_empty():
    with mock.patch.object(
        ctl.sdk.AgentsApi,
        "v1_network_agents_get",
        autospec=True,
        return_value=models.V1NetworkAgentsGetResponse([]),
    ) as the_mock:
        yield the_mock


@pytest.fixture
def mock_agents_search_empty():
    with mock.patch.object(
        ctl.sdk.AgentsApi,
        "v1_network_agents_search",
        autospec=True,
        return_value=models.V1NetworkAgentsSearchResponse([]),
    ) as the_mock:
        yield the_mock


@pytest.fixture
def agents_response_builder():
    def builder(data):
        response = models.V1NetworkAgentsGetResponse([])
        for id, i in enumerate(data):
            params = {
                "agent_id": 123 + id,
                "agent_provider": {"agent_provider_name": "provider"},
                "agent_public_ipv4": f"127.0.0.{1+id}",
                "agent_device_id": f"an id {id}",
                "agent_is_virtual": False,
                "agent_status": "CONNECTED",
                "agent_is_online": True,
                "agent_name": f"name_{id}",
                "agent_location_city": "city",
                "agent_location_country": "country",
                "agent_version": "v0.0.0a",
                "agent_locked_fields": "",
                "agent_modified_at": "",
                "agent_type": "",
                "agent_tags": [""],
                "agent_services_subnets_count": 1,
                "agent_services_subnets_enabled_count": 2,
            }
            params.update(i)
            response.data.append(models.V1Agent(**params))
        return response

    return builder


@pytest.fixture
def mock_agents_get_single(agents_response_builder):
    with mock.patch.object(
        ctl.sdk.AgentsApi,
        "v1_network_agents_get",
        autospec=True,
        return_value=agents_response_builder([{}]),
    ) as the_mock:
        yield the_mock


@pytest.fixture
def mock_agents_get_single_dict(agents_response_builder):
    with mock.patch.object(
        ctl.sdk.AgentsApi,
        "v1_network_agents_get",
        autospec=True,
        return_value=agents_response_builder([{}]).to_dict(),
    ) as the_mock:
        yield the_mock


@pytest.fixture
def mock_agents_search_single(agents_response_builder):
    with mock.patch.object(
        ctl.sdk.AgentsApi,
        "v1_network_agents_search",
        autospec=True,
        return_value=agents_response_builder([{}]),
    ) as the_mock:
        yield the_mock


@pytest.fixture
def mock_agents_search_single_dict(agents_response_builder):
    with mock.patch.object(
        ctl.sdk.AgentsApi,
        "v1_network_agents_search",
        autospec=True,
        return_value=agents_response_builder([{}]).to_dict(),
    ) as the_mock:
        yield the_mock


@pytest.fixture
def mock_agents_get():
    with mock.patch.object(
        ctl.sdk.AgentsApi,
        "v1_network_agents_get",
        autospec=True,
        return_value=models.V1NetworkAgentsGetResponse(
            [
                models.V1Agent(
                    agent_id=123,
                    agent_provider={"agent_provider_name": "provider"},
                    agent_public_ipv4="127.0.0.1",
                    agent_device_id="an id",
                    agent_is_virtual=False,
                    agent_status="ONLINE",
                    agent_is_online=True,
                    agent_name="name",
                    agent_location_city="city",
                    agent_location_country="country",
                    agent_version="v0.0.0a",
                    agent_locked_fields="",
                    agent_modified_at="",
                    agent_type="",
                    agent_tags=[""],
                    agent_services_subnets_count=1,
                    agent_services_subnets_enabled_count=2,
                ),
                models.V1Agent(
                    agent_id=234,
                    agent_provider=None,
                    agent_public_ipv4="127.0.0.1",
                    agent_device_id="an id",
                    agent_is_virtual=False,
                    agent_status="ONLINE",
                    agent_is_online=True,
                    agent_name="name",
                    agent_location_city="city",
                    agent_location_country="country",
                    agent_version="v0.0.0a",
                    agent_locked_fields="",
                    agent_modified_at="",
                    agent_type="",
                    agent_tags=[""],
                    agent_services_subnets_count=1,
                    agent_services_subnets_enabled_count=2,
                ),
                models.V1Agent(
                    agent_id=345,
                    agent_public_ipv4="127.0.0.1",
                    agent_device_id="an id",
                    agent_is_virtual=False,
                    agent_status="ONLINE",
                    agent_is_online=True,
                    agent_name="name",
                    agent_location_city="city",
                    agent_location_country="country",
                    agent_version="v0.0.0a",
                    agent_locked_fields="",
                    agent_modified_at="",
                    agent_type="",
                    agent_tags=[""],
                    agent_services_subnets_count=1,
                    agent_services_subnets_enabled_count=2,
                ),
                models.V1Agent(
                    agent_id=456,
                    agent_provider={},
                    agent_public_ipv4="127.0.0.1",
                    agent_device_id="an id",
                    agent_is_virtual=False,
                    agent_status="ONLINE",
                    agent_is_online=True,
                    agent_name="name",
                    agent_location_city="city",
                    agent_location_country="country",
                    agent_version="v0.0.0a",
                    agent_locked_fields="",
                    agent_modified_at="",
                    agent_type="",
                    agent_tags=[""],
                    agent_services_subnets_count=1,
                    agent_services_subnets_enabled_count=2,
                ),
                models.V1Agent(
                    agent_id=567,
                    agent_provider={"agent_provider_name": None},
                    agent_public_ipv4="127.0.0.1",
                    agent_device_id="an id",
                    agent_is_virtual=False,
                    agent_status="ONLINE",
                    agent_is_online=True,
                    agent_name="name",
                    agent_location_city="city",
                    agent_location_country="country",
                    agent_version="v0.0.0a",
                    agent_locked_fields="",
                    agent_modified_at="",
                    agent_type="",
                    agent_tags=[""],
                    agent_services_subnets_count=1,
                    agent_services_subnets_enabled_count=2,
                ),
            ]
        ),
    ) as the_mock:
        yield the_mock


@pytest.fixture
def mock_agents_services_get_empty():
    with mock.patch.object(
        ctl.sdk.AgentsApi,
        "v1_network_agents_services_get",
        autospec=True,
        return_value=models.V1NetworkAgentsServicesGetResponse([]),
    ) as the_mock:
        yield the_mock


@pytest.fixture
def mock_agents_services_get():
    with mock.patch.object(
        ctl.sdk.AgentsApi,
        "v1_network_agents_services_get",
        autospec=True,
        return_value=models.V1NetworkAgentsServicesGetResponse(
            [
                {
                    "agent_id": 123,
                    "agent_service_name": "abc",
                    "agent_service_is_active": True,
                    "agent_service_subnets": [
                        {
                            "agent_service_subnet_id": 1,
                            "agent_service_subnet_is_user_enabled": False,
                            "agent_service_subnet_is_active": True,
                        },
                    ],
                },
                {
                    "agent_id": 123,
                    "agent_service_name": "def",
                    "agent_service_is_active": True,
                    "agent_service_subnets": [
                        {
                            "agent_service_subnet_id": 2,
                            "agent_service_subnet_is_user_enabled": True,
                            "agent_service_subnet_is_active": True,
                        },
                    ],
                },
            ]
        ),
    ) as the_mock:
        yield the_mock
