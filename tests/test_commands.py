# coding: utf-8
import datetime
import os
import unittest
from unittest import mock

import pytest
import syntropy_sdk as sdk
from click.testing import CliRunner
from syntropy_sdk import models
from syntropy_sdk.rest import ApiException

from syntropycli import __main__ as ctl


@pytest.fixture
def confirm_deletion():
    with mock.patch(
        "syntropycli.__main__.confirm_deletion",
        autospec=True,
        side_effect=[False, True],
    ) as the_mock:
        yield the_mock


def test_get_providers(runner, print_table_mock, login_mock):
    with mock.patch.object(
        sdk.AgentsApi,
        "v1_network_agents_providers_get",
        autospec=True,
        return_value=models.V1NetworkAgentsProvidersGetResponse(
            [
                models.AgentProvider(
                    **{
                        "agent_provider_id": 1,
                        "agent_provider_name": "AWS",
                        "agent_provider_icon_url": "url 1",
                    }
                ),
                models.AgentProvider(
                    **{
                        "agent_provider_id": 2,
                        "agent_provider_name": "IBM",
                        "agent_provider_icon_url": "url 2",
                    }
                ),
                models.AgentProvider(
                    **{
                        "agent_provider_id": 3,
                        "agent_provider_name": "Unknown",
                        "agent_provider_icon_url": "url 3",
                    }
                ),
            ],
        ),
    ) as index_mock:
        runner.invoke(ctl.get_providers)
        index_mock.assert_called_once()
        print_table_mock.assert_called_once()


def test_get_api_keys(runner, print_table_mock, mock_index_api_key, login_mock):
    runner.invoke(ctl.get_api_keys)
    mock_index_api_key.assert_called_once()
    print_table_mock.assert_called_once()


def test_create_api_key(runner, mock_create_api_key, login_mock):
    runner.invoke(ctl.create_api_key, ["name", "a description", "2021-10-11 20:20:21"])
    mock_create_api_key.assert_called_once_with(
        mock.ANY,
        body=models.V1NetworkAuthApiKeysCreateRequest(
            api_key_name="name",
            api_key_valid_until=datetime.datetime(2021, 10, 11, 20, 20, 21),
            api_key_description="a description",
        ),
    )


def test_delete_api_key__by_id(runner, mock_delete_api_key, login_mock):
    runner.invoke(ctl.delete_api_key, ["--id", "123"])
    mock_delete_api_key.assert_called_once_with(mock.ANY, 123)


def test_delete_api_key__by_name(
    runner, confirm_deletion, mock_delete_api_key, mock_index_api_key, login_mock
):
    runner.invoke(ctl.delete_api_key, ["--name", "test"])
    mock_index_api_key.assert_called_once()
    assert mock_delete_api_key.call_count == 0
    assert confirm_deletion.call_count == 1


def test_delete_api_key__by_name_force(
    runner, confirm_deletion, mock_delete_api_key, mock_index_api_key, login_mock
):
    runner.invoke(ctl.delete_api_key, ["--name", "test", "--yes"])
    assert mock_delete_api_key.call_args_list == [
        mock.call(mock.ANY, 321),
    ]
    mock_index_api_key.assert_called_once()
    assert confirm_deletion.call_count == 0


def test_get_endpoints__empty(
    runner,
    print_table_mock,
    login_mock,
    mock_agents_search_empty,
    mock_agents_get_empty,
):
    runner.invoke(ctl.get_endpoints)
    mock_agents_get_empty.assert_called_once()
    assert mock_agents_search_empty.call_count == 0
    print_table_mock.assert_called_once()


@pytest.mark.parametrize(
    "args",
    [
        ["--name", "a name"],
        ["--id", "123"],
        ["--tag", "tag"],
    ],
)
def test_get_endpoints__filters_empty(
    runner,
    print_table_mock,
    login_mock,
    mock_agents_search_empty,
    mock_agents_get_empty,
    args,
):
    runner.invoke(ctl.get_endpoints, args)
    mock_agents_search_empty.assert_called_once()
    assert mock_agents_get_empty.call_count == 0
    print_table_mock.assert_called_once()


def test_get_endpoints__with_services(
    runner,
    print_table_mock,
    login_mock,
    mock_agents_get_single,
    mock_agents_services_get_empty,
):
    runner.invoke(ctl.get_endpoints, "--show-services")
    mock_agents_get_single.assert_called_once()
    mock_agents_services_get_empty.assert_called_once_with(
        mock.ANY, filter="123", _preload_content=False
    )
    print_table_mock.assert_called_once()


def test_configure_endpoints__none(
    runner,
    print_table_mock,
    login_mock,
    with_pagination,
    mock_agents_get_single,
    mock_agents_search_empty,
    mock_agents_services_get_empty,
):
    runner.invoke(ctl.configure_endpoints, "an-endpoint")
    assert mock_agents_search_empty.call_count == 1
    assert mock_agents_get_single.call_count == 0
    assert mock_agents_services_get_empty.call_count == 0
    assert print_table_mock.call_count == 0


@pytest.mark.parametrize(
    "args, patch_args",
    [
        [["123", "--add-tag", "abcd"], {"agent_tags": ["abcd"]}],
        [
            ["an-endpoint", "--name", "--set-provider", "another"],
            {"agent_provider_name": "another"},
        ],
        [
            ["an-endpoint", "-n", "--add-tag", "abcd", "--set-provider", "another"],
            {"agent_tags": ["abcd"], "agent_provider_name": "another"},
        ],
    ],
)
def test_configure_endpoints__tags_providers(
    runner,
    print_table_mock,
    args,
    patch_args,
    login_mock,
    with_pagination,
    mock_agents_search_single,
    mock_agents_get_single,
    mock_agents_services_get_empty,
):
    with mock.patch.object(
        ctl.sdk.AgentsApi,
        "v1_network_agents_update",
        autospec=True,
    ) as patch_mock:
        runner.invoke(ctl.configure_endpoints, args)
        assert mock_agents_get_single.call_count == 0
        assert mock_agents_search_single.call_count == 2
        assert patch_mock.call_args_list == [
            mock.call(mock.ANY, patch_args, 123),
        ]
        assert mock_agents_services_get_empty.call_count == 0
        print_table_mock.assert_called_once()


@pytest.mark.parametrize(
    "args, patch_args",
    [
        [
            ["an-endpoint", "--name", "--set-service", "abc"],
            [
                models.V1NetworkAgentsServicesUpdateRequestSubnetsToUpdate(
                    agent_service_subnet_id=1, is_enabled=True
                ),
                models.V1NetworkAgentsServicesUpdateRequestSubnetsToUpdate(
                    agent_service_subnet_id=2, is_enabled=False
                ),
            ],
        ],
        [
            ["an-endpoint", "-n", "--enable-service", "abc"],
            [
                models.V1NetworkAgentsServicesUpdateRequestSubnetsToUpdate(
                    agent_service_subnet_id=1, is_enabled=True
                )
            ],
        ],
        [
            ["an-endpoint", "-n", "--disable-service", "def"],
            [
                models.V1NetworkAgentsServicesUpdateRequestSubnetsToUpdate(
                    agent_service_subnet_id=2, is_enabled=False
                )
            ],
        ],
        [
            ["an-endpoint", "-n", "--enable-all-services"],
            [
                models.V1NetworkAgentsServicesUpdateRequestSubnetsToUpdate(
                    agent_service_subnet_id=1, is_enabled=True
                )
            ],
        ],
        [
            ["an-endpoint", "-n", "--disable-all-services"],
            [
                models.V1NetworkAgentsServicesUpdateRequestSubnetsToUpdate(
                    agent_service_subnet_id=2, is_enabled=False
                )
            ],
        ],
    ],
)
def test_configure_endpoints__services(
    runner,
    print_table_mock,
    args,
    patch_args,
    login_mock,
    with_pagination,
    mock_agents_search_single,
    mock_agents_services_get,
):
    with mock.patch.object(
        ctl.sdk.AgentsApi,
        "v1_network_agents_services_update",
        autospec=True,
    ) as patch_mock:
        runner.invoke(ctl.configure_endpoints, args)
        assert mock_agents_search_single.call_count == 2
        patch_mock.assert_called_once_with(
            mock.ANY,
            models.V1NetworkAgentsServicesUpdateRequest(subnets_to_update=patch_args),
        )
        assert mock_agents_services_get.call_count == 2
        print_table_mock.assert_called_once()


def test_get_connections(runner, print_table_mock, login_mock):
    with mock.patch.object(
        ctl.sdk.ConnectionsApi,
        "v1_network_connections_get",
        autospec=True,
        return_value=models.V1NetworkConnectionsGetResponse([]),
    ) as index_mock:
        runner.invoke(ctl.get_connections)
        index_mock.assert_called_once()
        print_table_mock.assert_called_once()


def test_get_connections__with_services(runner, print_table_mock, login_mock):
    with mock.patch.object(
        ctl.sdk.ConnectionsApi,
        "v1_network_connections_get",
        autospec=True,
        return_value={"data": [{"agent_connection_group_id": 123}]},
    ) as index_mock:
        with mock.patch.object(
            ctl.sdk.ConnectionsApi,
            "v1_network_connections_services_get",
            autospec=True,
            return_value={"data": [{"agent_connection_group_id": 123}]},
        ) as services_mock:
            res = runner.invoke(ctl.get_connections, "--show-services")
            index_mock.assert_called_once()
            services_mock.assert_called_once_with(
                mock.ANY, filter="123", _preload_content=False
            )
            print_table_mock.assert_called_once()


def test_create_connections__p2p(runner, login_mock):
    with mock.patch.object(
        ctl.sdk.ConnectionsApi,
        "v1_network_connections_create_p2_p",
        autospec=True,
        return_value={"data": []},
    ) as the_mock:
        runner.invoke(ctl.create_connections, ["1", "2", "3", "4"])
        the_mock.assert_called_once_with(
            mock.ANY,
            body=models.V1NetworkConnectionsCreateP2PRequest(
                agent_pairs=[
                    models.V1NetworkConnectionsCreateP2PRequestAgentPairs(
                        agent_1_id=1,
                        agent_2_id=2,
                    ),
                    models.V1NetworkConnectionsCreateP2PRequestAgentPairs(
                        agent_1_id=3,
                        agent_2_id=4,
                    ),
                ],
            ),
            _preload_content=False,
        )


def test_create_connections__p2p__fail(runner, login_mock):
    with mock.patch.object(
        ctl.sdk.ConnectionsApi,
        "v1_network_connections_create_p2_p",
        autospec=True,
        return_value={"errors": [{"message": "some error"}]},
    ) as the_mock:
        result = runner.invoke(ctl.create_connections, ["1", "2", "3", "4"])
        the_mock.assert_called_once_with(
            mock.ANY,
            body=models.V1NetworkConnectionsCreateP2PRequest(
                agent_pairs=[
                    models.V1NetworkConnectionsCreateP2PRequestAgentPairs(
                        agent_1_id=1,
                        agent_2_id=2,
                    ),
                    models.V1NetworkConnectionsCreateP2PRequestAgentPairs(
                        agent_1_id=3,
                        agent_2_id=4,
                    ),
                ],
            ),
            _preload_content=False,
        )
        assert "some error" in result.output


def test_create_connections__p2p_by_name(runner, login_mock):
    with mock.patch.object(
        ctl.sdk.AgentsApi,
        "v1_network_agents_get",
        autospec=True,
        return_value={
            "data": [
                {"agent_id": 1, "agent_name": "a"},
                {"agent_id": 2, "agent_name": "b"},
            ]
        },
    ) as index_mock:
        with mock.patch.object(
            ctl.sdk.ConnectionsApi,
            "v1_network_connections_create_p2_p",
            autospec=True,
            return_value={"data": []},
        ) as the_mock:
            runner.invoke(
                ctl.create_connections,
                ["--use-names", "a", "b"],
            )
            index_mock.assert_called_once()
            the_mock.assert_called_once_with(
                mock.ANY,
                body=models.V1NetworkConnectionsCreateP2PRequest(
                    agent_pairs=[
                        models.V1NetworkConnectionsCreateP2PRequestAgentPairs(
                            agent_1_id=1,
                            agent_2_id=2,
                        ),
                    ],
                ),
                _preload_content=False,
            )


def test_delete_connection(runner, login_mock):
    with mock.patch.object(
        ctl.sdk.ConnectionsApi, "v1_network_connections_delete", autospec=True
    ) as the_mock:
        runner.invoke(ctl.delete_connection, "123")
        the_mock.assert_called_once_with(
            mock.ANY,
            123,
        )


def test_delete_connection__multiple(runner, login_mock):
    with mock.patch.object(
        ctl.sdk.ConnectionsApi, "v1_network_connections_delete", autospec=True
    ) as the_mock:
        runner.invoke(ctl.delete_connection, ["123", "345"])
        assert the_mock.call_args_list == [
            mock.call(mock.ANY, 123),
            mock.call(mock.ANY, 345),
        ]
