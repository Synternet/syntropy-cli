# coding: utf-8
import datetime
import os
import unittest
from unittest import mock

import pytest
import syntropy_sdk as sdk
from click.testing import CliRunner
from syntropy_sdk.rest import ApiException

from syntropycli import __main__ as ctl


@pytest.fixture
def env_mock():
    with mock.patch.dict(os.environ, {"SYNTROPY_API_SERVER": "server"}) as the_mock:
        yield the_mock


@pytest.fixture
def api_lock_fix(env_mock):
    api_del = ctl.sdk.ApiClient.__del__
    ctl.sdk.ApiClient.__del__ = lambda x: x
    yield
    # NOTE: We don't restore __del__ for api client since there is a known issue with locking pool.
    # ctl.sdk.ApiClient.__del__ = api_del


@pytest.fixture
def runner(api_lock_fix):
    return CliRunner()


@pytest.fixture
def print_table_mock():
    with mock.patch(
        "syntropycli.__main__.print_table",
        autospec=True,
    ) as the_mock:
        yield the_mock


def testLogin(runner):
    with mock.patch.object(
        ctl.sdk.AuthApi,
        "local",
        autospec=True,
        return_value={"refresh_token": "token"},
    ) as the_mock:
        result = runner.invoke(ctl.login, ["username", "password"])
        assert result.stdout.rstrip() == "token"
        the_mock.assert_called_once_with(
            mock.ANY,
            body={
                "user_email": "username",
                "user_password": "password",
                "additionalProp1": {},
            },
        )


def testGetApiKeys(runner, print_table_mock):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "index_api_key",
        autospec=True,
        return_value={"data": []},
    ) as index_mock:
        runner.invoke(ctl.get_api_keys)
        index_mock.assert_called_once()
        print_table_mock.assert_called_once()


def testCreateApiKey(runner):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "create_api_key",
        autospec=True,
        return_value={"data": {"api_key_id": 123}},
    ) as the_mock:
        runner.invoke(
            ctl.create_api_key, ["name", "2021-10-11 20:20:21", "--suspended"]
        )
        the_mock.assert_called_once_with(
            mock.ANY,
            body={
                "api_key_name": "name",
                "api_key_is_suspended": True,
                "api_key_valid_until": datetime.datetime(2021, 10, 11, 20, 20, 21),
            },
        )


def testDeleteApiKeyById(runner):
    with mock.patch.object(
        ctl.sdk.PlatformApi, "delete_api_key", autospec=True
    ) as the_mock:
        runner.invoke(ctl.delete_api_key, ["--id", "123"])
        the_mock.assert_called_once_with(mock.ANY, 123)


def testDeleteApiKeyByName(runner):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "index_api_key",
        autospec=True,
        return_value={
            "data": [
                {"api_key_name": "skip", "api_key_id": 321},
                {"api_key_name": "test", "api_key_id": 123},
            ]
        },
    ) as index_mock:
        with mock.patch.object(
            ctl.sdk.PlatformApi, "delete_api_key", autospec=True
        ) as the_mock:
            runner.invoke(ctl.delete_api_key, ["--name", "test"])
            the_mock.assert_called_once_with(mock.ANY, 123)
            index_mock.assert_called_once()


def testGetEndpoints(runner, print_table_mock):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "index_agents",
        autospec=True,
        return_value={"data": []},
    ) as index_mock:
        runner.invoke(ctl.get_endpoints)
        index_mock.assert_called_once()
        print_table_mock.assert_called_once()


def testGetEndpointsServices(runner, print_table_mock):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "index_agents",
        autospec=True,
        return_value={
            "data": [
                {
                    "agent_id": 123,
                }
            ]
        },
    ) as index_mock:
        with mock.patch.object(
            ctl.sdk.PlatformApi,
            "get_agent_services_with_subnets",
            autospec=True,
            return_value={"data": []},
        ) as services_mock:
            runner.invoke(ctl.get_endpoints, "--show-services")
            index_mock.assert_called_once()
            services_mock.assert_called_once_with(mock.ANY, [123])
            print_table_mock.assert_called_once()


def testGetTopology(runner, print_table_mock):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "topology_networks",
        autospec=True,
        return_value={"data": []},
    ) as index_mock:
        runner.invoke(ctl.get_topology)
        index_mock.assert_called_once()
        print_table_mock.assert_called_once()


def testGetConnections(runner, print_table_mock):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "index_connections",
        autospec=True,
        return_value={"data": []},
    ) as index_mock:
        runner.invoke(ctl.get_connections)
        index_mock.assert_called_once()
        print_table_mock.assert_called_once()


def testGetConnectionsServices(runner, print_table_mock):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "index_connections",
        autospec=True,
        return_value={"data": [{"agent_connection_id": 123}]},
    ) as index_mock:
        with mock.patch.object(
            ctl.sdk.PlatformApi,
            "get_connection_services",
            autospec=True,
            return_value={"data": [{"agent_connection_id": 123}]},
        ) as services_mock:
            runner.invoke(ctl.get_connections, "--show-services")
            index_mock.assert_called_once()
            services_mock.assert_called_once_with(mock.ANY, [123])
            print_table_mock.assert_called_once()


def testCreateConnectionsP2P(runner, print_table_mock):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "index_networks",
        autospec=True,
        return_value={"data": [{"network_id": 123, "network_type": "POINT_TO_POINT"}]},
    ) as index_mock:
        with mock.patch.object(
            ctl.sdk.PlatformApi,
            "create_connections",
            autospec=True,
            return_value={"data": []},
        ) as the_mock:
            runner.invoke(ctl.create_connections, ["123", "1", "2", "3", "4"])
            index_mock.assert_called_once()
            the_mock.assert_called_once_with(
                mock.ANY,
                body={
                    "network_id": 123,
                    "agent_ids": [(1, 2), (3, 4)],
                    "network_update_by": sdk.NetworkGenesisType.SDK,
                },
            )
            print_table_mock.assert_called_once()


def testCreateConnectionsMesh(runner, print_table_mock):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "index_networks",
        autospec=True,
        return_value={"data": [{"network_id": 123, "network_type": "MESH"}]},
    ) as index_mock:
        with mock.patch.object(
            ctl.sdk.PlatformApi,
            "create_connections",
            autospec=True,
            return_value={"data": []},
        ) as the_mock:
            runner.invoke(ctl.create_connections, ["123", "1", "2", "3", "4"])
            index_mock.assert_called_once()
            the_mock.assert_called_once_with(
                mock.ANY,
                body={
                    "network_id": 123,
                    "agent_ids": [1, 2, 3, 4],
                    "network_update_by": sdk.NetworkGenesisType.SDK,
                },
            )
            print_table_mock.assert_called_once()


def testCreateConnectionsP2PByName(runner, print_table_mock):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "index_networks",
        autospec=True,
        return_value={
            "data": [
                {
                    "network_id": 123,
                    "network_name": "test",
                    "network_type": "POINT_TO_POINT",
                }
            ]
        },
    ) as index_mock:
        with mock.patch.object(
            ctl.sdk.PlatformApi,
            "index_agents",
            autospec=True,
            return_value={
                "data": [
                    {"agent_id": 1, "agent_name": "a"},
                    {"agent_id": 2, "agent_name": "b"},
                ]
            },
        ) as index_mock:
            with mock.patch.object(
                ctl.sdk.PlatformApi,
                "create_connections",
                autospec=True,
                return_value={"data": []},
            ) as the_mock:
                runner.invoke(
                    ctl.create_connections,
                    ["--use-names", "test", "a", "b"],
                )
                index_mock.assert_called_once()
                the_mock.assert_called_once_with(
                    mock.ANY,
                    body={
                        "network_id": 123,
                        "agent_ids": [(1, 2)],
                        "network_update_by": sdk.NetworkGenesisType.SDK,
                    },
                )
                print_table_mock.assert_called_once()


def testDeleteConnection(runner):
    with mock.patch.object(
        ctl.sdk.PlatformApi, "delete_connection", autospec=True
    ) as the_mock:
        runner.invoke(ctl.delete_connection, ["123"])
        the_mock.assert_called_once_with(mock.ANY, 123)


def testGetNetworks(runner, print_table_mock):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "index_networks",
        autospec=True,
        return_value={"data": []},
    ) as index_mock:
        runner.invoke(ctl.get_networks)
        index_mock.assert_called_once()
        print_table_mock.assert_called_once()


@pytest.mark.parametrize(
    "topology",
    [
        "P2P",
        "P2M",
        "MESH",
    ],
)
@pytest.mark.parametrize(
    "network_type",
    [
        "POINT_TO_POINT",
        "MESH",
        "GATEWAY",
    ],
)
def testCreateNetwork(runner, topology, network_type):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "create_network",
        autospec=True,
        return_value={"data": {"network_id": 123}},
    ) as the_mock:
        runner.invoke(
            ctl.create_network,
            [
                "name",
                "--network-type",
                network_type,
                "--topology",
                topology,
                "--gateway-id",
                "123",
            ],
        )
        the_mock.assert_called_once_with(
            mock.ANY,
            body={
                "network_name": "name",
                "network_type": network_type,
                "agent_gateway_id": 123,
                "network_disable_sdn_connections": True,
                "network_metadata": {
                    "network_type": topology,
                    "network_created_by": "SDK",
                },
            },
        )


def testManageNetworkEndpointsShow(runner):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "index_networks",
        autospec=True,
        return_value={
            "data": [
                {
                    "network_id": 123,
                    "network_name": "test",
                }
            ]
        },
    ):
        with mock.patch.object(
            ctl.sdk.PlatformApi,
            "get_network_info",
            autospec=True,
            return_value={
                "data": {
                    "network": {
                        "network_id": 123,
                        "network_name": "test",
                    },
                    "network_agents": [
                        {
                            "agent": {
                                "agent_id": 1,
                                "agent_name": "agent1",
                                "agent_public_ipv4": "127.0.0.1",
                            }
                        }
                    ],
                }
            },
        ):
            result = runner.invoke(ctl.manage_network_endpoints, "test")
            assert "test" in result.output
            assert "agent1" in result.output
            assert "127.0.0.1" in result.output


@pytest.mark.parametrize("agent_name, use_names", [["1", False], ["agent1", True]])
def testManageNetworkEndpointsRemove(runner, agent_name, use_names):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "index_networks",
        autospec=True,
        return_value={
            "data": [
                {
                    "network_id": 123,
                    "network_name": "test",
                }
            ]
        },
    ):
        with mock.patch.object(
            ctl.sdk.PlatformApi,
            "get_network_info",
            autospec=True,
            return_value={
                "data": {
                    "network": {
                        "network_id": 123,
                        "network_name": "test",
                    },
                    "network_agents": [
                        {
                            "agent": {
                                "agent_id": 1,
                                "agent_name": "agent1",
                                "agent_public_ipv4": "127.0.0.1",
                            }
                        }
                    ],
                }
            },
        ) as info_mock:
            with mock.patch.object(
                ctl.sdk.PlatformApi,
                "remove_network_agents",
                autospec=True,
            ) as remove_mock:
                runner.invoke(
                    ctl.manage_network_endpoints,
                    ["test", "-r", agent_name, "--use-names"]
                    if use_names
                    else ["test", "-r", agent_name],
                )
                remove_mock.assert_called_once_with(mock.ANY, [1], 123)
                assert info_mock.call_count == 2


@pytest.mark.parametrize("agent_name, use_names", [["1", False], ["agent1", True]])
def testManageNetworkEndpointsAdd(runner, agent_name, use_names):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "index_networks",
        autospec=True,
        return_value={
            "data": [
                {
                    "network_id": 123,
                    "network_name": "test",
                }
            ]
        },
    ):
        with mock.patch.object(
            ctl.sdk.PlatformApi,
            "index_agents",
            autospec=True,
            return_value={
                "data": [
                    {
                        "agent_id": 324,
                        "agent_name": "agent_name",
                    }
                ]
            },
        ) as index_mock:
            with mock.patch.object(
                ctl.sdk.PlatformApi,
                "get_network_info",
                autospec=True,
                return_value={
                    "data": {
                        "network": {
                            "network_id": 123,
                            "network_name": "test",
                        },
                        "network_agents": [
                            {
                                "agent": {
                                    "agent_id": 1,
                                    "agent_name": "agent1",
                                    "agent_public_ipv4": "127.0.0.1",
                                }
                            }
                        ],
                    }
                },
            ) as info_mock:
                with mock.patch.object(
                    ctl.sdk.PlatformApi,
                    "create_network_agents",
                    autospec=True,
                ) as add_mock:
                    runner.invoke(
                        ctl.manage_network_endpoints,
                        ["test", "-a", agent_name, "--use-names"]
                        if use_names
                        else ["test", "-a", agent_name],
                    )
                    add_mock.assert_called_once_with(
                        mock.ANY,
                        [
                            {
                                "agent_id": 324,
                            },
                        ],
                        123,
                    )
                    assert info_mock.call_count == 2
                    index_mock.assert_called_once_with(
                        mock.ANY,
                        filter=f"name:{agent_name}"
                        if use_names
                        else f"ids[]:{agent_name}",
                        load_relations=False,
                    )


def testCreateNetworkDefault(runner):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "create_network",
        autospec=True,
        return_value={"data": {"network_id": 123}},
    ) as the_mock:
        runner.invoke(
            ctl.create_network,
            [
                "name",
            ],
        )
        the_mock.assert_called_once_with(
            mock.ANY,
            body={
                "network_name": "name",
                "network_type": "POINT_TO_POINT",
                "agent_gateway_id": 0,
                "network_disable_sdn_connections": True,
                "network_metadata": {
                    "network_type": "P2P",
                    "network_created_by": "SDK",
                },
            },
        )


def testDeleteNetworkMultiple(runner):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "index_networks",
        autospec=True,
        return_value={
            "data": [
                {"network_name": "test", "network_id": 321},
                {"network_name": "test", "network_id": 123},
            ]
        },
    ) as index_mock:
        with mock.patch.object(
            ctl.sdk.PlatformApi, "delete_networks", autospec=True
        ) as the_mock:
            runner.invoke(ctl.delete_network, ["test"])
            assert the_mock.call_args_list == [
                mock.call(mock.ANY, 321),
                mock.call(mock.ANY, 123),
            ]
            index_mock.assert_called_once_with(mock.ANY, filter="id|name:test")
