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
def confirm_deletion():
    with mock.patch(
        "syntropycli.__main__.confirm_deletion",
        autospec=True,
        side_effect=[False, True],
    ) as the_mock:
        yield the_mock


def test_login(runner):
    with mock.patch.object(
        ctl.sdk.AuthApi,
        "auth_local_login",
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


def test_get_providers(runner, print_table_mock):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "platform_agent_provider_index",
        autospec=True,
        return_value={
            "data": [
                {
                    "agent_provider_id": 1,
                    "agent_provider_name": "AWS",
                    "agent_provider_tunnels_required": True,
                    "agent_provider_created_at": "2019-12-12T15:51:06.905",
                    "agent_provider_updated_at": "2019-12-12T15:51:06.905",
                },
                {
                    "agent_provider_id": 2,
                    "agent_provider_name": "IBM",
                    "agent_provider_tunnels_required": True,
                    "agent_provider_created_at": "2020-01-22T15:50:55.325",
                    "agent_provider_updated_at": "2020-01-22T15:50:55.325",
                },
                {
                    "agent_provider_id": 3,
                    "agent_provider_name": "Unknown",
                    "agent_provider_tunnels_required": True,
                    "agent_provider_created_at": "2020-09-21T07:48:50.111",
                    "agent_provider_updated_at": "2020-09-21T07:48:50.111",
                },
            ],
        },
    ) as index_mock:
        result = runner.invoke(ctl.get_providers)
        index_mock.assert_called_once()
        print_table_mock.assert_called_once()


def test_get_api_keys(runner, print_table_mock):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "platform_api_key_index",
        autospec=True,
        return_value={"data": []},
    ) as index_mock:
        runner.invoke(ctl.get_api_keys)
        index_mock.assert_called_once()
        print_table_mock.assert_called_once()


def test_create_api_key(runner):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "platform_api_key_create",
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


def test_delete_api_key__by_id(runner):
    with mock.patch.object(
        ctl.sdk.PlatformApi, "platform_api_key_destroy", autospec=True
    ) as the_mock:
        runner.invoke(ctl.delete_api_key, ["--id", "123"])
        the_mock.assert_called_once_with(mock.ANY, 123)


def test_delete_api_key__by_name(runner, confirm_deletion):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "platform_api_key_index",
        autospec=True,
        return_value={
            "data": [
                {"api_key_name": "skip", "api_key_id": 321},
                {"api_key_name": "test", "api_key_id": 123},
            ]
        },
    ) as index_mock:
        with mock.patch.object(
            ctl.sdk.PlatformApi, "platform_api_key_destroy", autospec=True
        ) as the_mock:
            runner.invoke(ctl.delete_api_key, ["--name", "test"])
            the_mock.assert_called_once_with(mock.ANY, 123)
            index_mock.assert_called_once()
            assert confirm_deletion.call_count == 2


def test_delete_api_key__by_name_force(runner, confirm_deletion):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "platform_api_key_index",
        autospec=True,
        return_value={
            "data": [
                {"api_key_name": "skip", "api_key_id": 321},
                {"api_key_name": "test", "api_key_id": 123},
            ]
        },
    ) as index_mock:
        with mock.patch.object(
            ctl.sdk.PlatformApi, "platform_api_key_destroy", autospec=True
        ) as the_mock:
            runner.invoke(ctl.delete_api_key, ["--name", "test", "--yes"])
            assert the_mock.call_args_list == [
                mock.call(mock.ANY, 321),
                mock.call(mock.ANY, 123),
            ]
            index_mock.assert_called_once()
            assert confirm_deletion.call_count == 0


def test_get_endpoints(runner, print_table_mock):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "platform_agent_index",
        autospec=True,
        return_value={"data": []},
    ) as index_mock:
        runner.invoke(ctl.get_endpoints)
        index_mock.assert_called_once()
        print_table_mock.assert_called_once()


def test_get_endpoints__with_services(runner, print_table_mock):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "platform_agent_index",
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
            "platform_agent_service_index",
            autospec=True,
            return_value={"data": []},
        ) as services_mock:
            runner.invoke(ctl.get_endpoints, "--show-services")
            index_mock.assert_called_once()
            services_mock.assert_called_once_with(mock.ANY, [123])
            print_table_mock.assert_called_once()


def test_configure_endpoints__none(runner, print_table_mock):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "platform_agent_index",
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
            "platform_agent_service_index",
            autospec=True,
            return_value={"data": []},
        ) as services_mock:
            runner.invoke(ctl.configure_endpoints, "an-endpoint")
            assert index_mock.call_count == 2
            assert services_mock.call_count == 0
            print_table_mock.assert_called_once()


@pytest.mark.parametrize(
    "args, patch_args",
    [
        [["an-endpoint", "--add-tag", "abcd"], {"agent_tags": ["abcd"]}],
        [
            ["an-endpoint", "--set-provider", "another"],
            {"agent_provider_name": "another"},
        ],
        [
            ["an-endpoint", "--add-tag", "abcd", "--set-provider", "another"],
            {"agent_tags": ["abcd"], "agent_provider_name": "another"},
        ],
    ],
)
def test_configure_endpoints_tags(runner, print_table_mock, args, patch_args):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "platform_agent_index",
        autospec=True,
        return_value={
            "data": [
                {
                    "agent_id": 123,
                    "agent_provider": {"agent_provider_name": "provider"},
                }
            ]
        },
    ) as index_mock:
        with mock.patch.object(
            ctl.sdk.PlatformApi,
            "platform_agent_service_index",
            autospec=True,
            return_value={"data": []},
        ) as services_mock:
            with mock.patch.object(
                ctl.sdk.PlatformApi,
                "platform_agent_update",
                autospec=True,
            ) as patch_mock:
                runner.invoke(ctl.configure_endpoints, args)
                assert index_mock.call_count == 2
                patch_mock.assert_called_once_with(mock.ANY, patch_args, 123)
                assert services_mock.call_count == 0
                print_table_mock.assert_called_once()


@pytest.mark.parametrize(
    "args, patch_args",
    [
        [
            ["an-endpoint", "--set-service", "abc"],
            [{"id": 1, "isEnabled": True}, {"id": 2, "isEnabled": False}],
        ],
        [
            ["an-endpoint", "--enable-service", "abc"],
            [{"id": 1, "isEnabled": True}],
        ],
        [
            ["an-endpoint", "--disable-service", "def"],
            [{"id": 2, "isEnabled": False}],
        ],
        [["an-endpoint", "--enable-all-services"], [{"id": 1, "isEnabled": True}]],
        [
            ["an-endpoint", "--disable-all-services"],
            [{"id": 2, "isEnabled": False}],
        ],
    ],
)
def test_configure_endpoints_services(runner, print_table_mock, args, patch_args):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "platform_agent_index",
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
            "platform_agent_service_index",
            autospec=True,
            return_value={
                "data": [
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
            },
        ) as services_mock:
            with mock.patch.object(
                ctl.sdk.PlatformApi,
                "platform_agent_service_subnet_update",
                autospec=True,
            ) as patch_mock:
                runner.invoke(ctl.configure_endpoints, args)
                assert index_mock.call_count == 2
                patch_mock.assert_called_once_with(
                    mock.ANY, {"subnetsToUpdate": patch_args}
                )
                assert services_mock.call_count == 2
                print_table_mock.assert_called_once()


def test_get_topology(runner, print_table_mock):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "platform_network_topology",
        autospec=True,
        return_value={"data": []},
    ) as index_mock:
        runner.invoke(ctl.get_topology)
        index_mock.assert_called_once()
        print_table_mock.assert_called_once()


def test_get_connections(runner, print_table_mock):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "platform_connection_index",
        autospec=True,
        return_value={"data": []},
    ) as index_mock:
        runner.invoke(ctl.get_connections)
        index_mock.assert_called_once()
        print_table_mock.assert_called_once()


def test_get_connections__with_services(runner, print_table_mock):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "platform_connection_index",
        autospec=True,
        return_value={"data": [{"agent_connection_id": 123}]},
    ) as index_mock:
        with mock.patch.object(
            ctl.sdk.PlatformApi,
            "platform_connection_service_show",
            autospec=True,
            return_value={"data": [{"agent_connection_id": 123}]},
        ) as services_mock:
            runner.invoke(ctl.get_connections, "--show-services")
            index_mock.assert_called_once()
            services_mock.assert_called_once_with(mock.ANY, [123])
            print_table_mock.assert_called_once()


def test_create_connections__p2p(runner, print_table_mock):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "platform_network_index",
        autospec=True,
        return_value={"data": [{"network_id": 123, "network_type": "POINT_TO_POINT"}]},
    ) as index_mock:
        with mock.patch.object(
            ctl.sdk.PlatformApi,
            "platform_connection_create",
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
                update_type=sdk.UpdateType.APPEND_NEW,
            )
            print_table_mock.assert_called_once()


def test_create_connections__mesh(runner, print_table_mock):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "platform_network_index",
        autospec=True,
        return_value={"data": [{"network_id": 123, "network_type": "MESH"}]},
    ) as index_mock:
        with mock.patch.object(
            ctl.sdk.PlatformApi,
            "platform_connection_create",
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
                update_type=sdk.UpdateType.APPEND_NEW,
            )
            print_table_mock.assert_called_once()


def test_create_connections__p2p_by_name(runner, print_table_mock):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "platform_network_index",
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
            "platform_agent_index",
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
                "platform_connection_create",
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
                    update_type=sdk.UpdateType.APPEND_NEW,
                )
                print_table_mock.assert_called_once()


def test_delete_connection(runner):
    with mock.patch.object(
        ctl.sdk.PlatformApi, "platform_connection_destroy", autospec=True
    ) as the_mock:
        runner.invoke(ctl.delete_connection, ["123"])
        the_mock.assert_called_once_with(mock.ANY, 123)


def test_get_networks(runner, print_table_mock):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "platform_network_index",
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
def test_create_network(runner, topology, network_type):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "platform_network_create",
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


def test_manage_network_endpoints__show(runner):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "platform_network_index",
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
            "platform_network_info",
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
def test_manage_network_endpoints__remove(runner, agent_name, use_names):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "platform_network_index",
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
            "platform_network_info",
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
                "platform_network_agent_destroy",
                autospec=True,
            ) as remove_mock:
                runner.invoke(
                    ctl.manage_network_endpoints,
                    ["test", "-r", agent_name, "--use-names"]
                    if use_names
                    else ["test", "-r", agent_name],
                )
                remove_mock.assert_called_once_with(mock.ANY, 123, 1)
                assert info_mock.call_count == 2


@pytest.mark.parametrize("agent_name, use_names", [["1", False], ["agent1", True]])
def test_manage_network_endpoints__add(runner, agent_name, use_names):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "platform_network_index",
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
            "platform_agent_index",
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
                "platform_network_info",
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
                    "platform_network_agent_create",
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
                        filter=f"name:'{agent_name}'"
                        if use_names
                        else f"ids[]:{agent_name}",
                        load_relations=False,
                    )


def test_create_network__default(runner):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "platform_network_create",
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


def test_delete_network__multiple(runner, confirm_deletion):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "platform_network_index",
        autospec=True,
        return_value={
            "data": [
                {"network_name": "test", "network_id": 321},
                {"network_name": "test", "network_id": 123},
            ]
        },
    ) as index_mock:
        with mock.patch.object(
            ctl.sdk.PlatformApi, "platform_network_destroy", autospec=True
        ) as the_mock:
            runner.invoke(ctl.delete_network, ["test"])
            assert the_mock.call_args_list == [
                mock.call(mock.ANY, 123),
            ]
            index_mock.assert_called_once_with(mock.ANY, filter="id|name:'test'")
            assert confirm_deletion.call_count == 2


def test_delete_network__multiple_forced(runner, confirm_deletion):
    with mock.patch.object(
        ctl.sdk.PlatformApi,
        "platform_network_index",
        autospec=True,
        return_value={
            "data": [
                {"network_name": "test", "network_id": 321},
                {"network_name": "test", "network_id": 123},
            ]
        },
    ) as index_mock:
        with mock.patch.object(
            ctl.sdk.PlatformApi, "platform_network_destroy", autospec=True
        ) as the_mock:
            runner.invoke(ctl.delete_network, ["test", "--yes"])
            assert the_mock.call_args_list == [
                mock.call(mock.ANY, 321),
                mock.call(mock.ANY, 123),
            ]
            index_mock.assert_called_once_with(mock.ANY, filter="id|name:'test'")
            assert confirm_deletion.call_count == 0
