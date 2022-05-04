# coding: utf-8

import datetime
import unittest
from unittest import mock

import pytest
import syntropy_sdk as sdk
from click.testing import CliRunner
from syntropy_sdk.rest import ApiException

from syntropycli import utils


def test_print_table():
    items = [
        {"a": 123, "b": 321, "c": {"ac": 1, "bc": None}},
        {"a": 111, "b": 222},
    ]
    fields = [
        ("A", "a"),
        ("B", "b", lambda x: x * 10),
        ("C->A", ("c", "ac")),
        ("C->B", ("c", "bc")),
    ]
    table_mock = mock.Mock(spec=utils.PrettyTable)
    with mock.patch("syntropycli.utils.PrettyTable", return_value=table_mock):
        utils.print_table(items, fields)
        assert table_mock.field_names == ["A", "B", "C->A", "C->B"]
        assert table_mock.add_row.call_args_list == [
            mock.call(
                [123, 3210, 1, "-"],
            ),
            mock.call(
                [111, 2220, "-", "-"],
            ),
        ]


def test_print_table__json():
    items = [
        {"a": 123, "b": 321, "c": {"ac": 1, "bc": None}},
        {"a": 111, "b": 222},
    ]
    fields = []
    table_mock = mock.Mock(spec=utils.json)
    with mock.patch(
        "syntropycli.utils.json.dumps", return_value=table_mock
    ) as the_mock:
        utils.print_table(items, fields, to_json=True)
        the_mock.assert_called_once_with(items, indent=4, default=str)


def test_find_by_name():
    items = [
        {"test_id": 1, "test_name": "name"},
        {"test_id": 2, "test_name": "name1"},
    ]
    assert utils.find_by_name(items, "name1", "test") == 2


def test_find_by_name__list():
    items = [
        {"test_id": 1, "test_name": "name"},
        {"test_id": 2, "test_name": "name1"},
    ]
    assert utils.find_by_name(items, ["name1", "name"], "test") == [2, 1]


def test_find_by_name__list__not_found():
    items = [
        {"test_id": 1, "test_name": "name"},
        {"test_id": 2, "test_name": "name1"},
    ]
    assert utils.find_by_name(items, ["test", "name1", "name"], "test") == [
        None,
        2,
        1,
    ]


def test_find_by_name__not_found():
    items = [
        {"test_id": 1, "test_name": "name"},
        {"test_id": 2, "test_name": "name1"},
    ]
    assert utils.find_by_name(items, "test3", "test") is None


def test_find_by_name__no_field():
    items = [
        {"test_id": 1, "test_name": "name"},
        {"test_id": 2, "test_name": "name1"},
    ]
    assert utils.find_by_name(items, "test3", "test") is None


def test_collect_endpoint_services():
    agent_services = [
        {
            "agent_service_name": "a",
            "agent_service_is_active": True,
            "agent_service_subnets": [
                {
                    "agent_service_subnet_is_active": True,
                    "agent_service_subnet_is_user_enabled": True,
                },
                {
                    "agent_service_subnet_is_active": True,
                    "agent_service_subnet_is_user_enabled": True,
                },
            ],
        },
        {
            "agent_service_name": "b",
            "agent_service_is_active": False,
            "agent_service_subnets": [
                {
                    "agent_service_subnet_is_active": True,
                    "agent_service_subnet_is_user_enabled": True,
                },
                {
                    "agent_service_subnet_is_active": True,
                    "agent_service_subnet_is_user_enabled": True,
                },
            ],
        },
        {
            "agent_service_name": "c",
            "agent_service_is_active": True,
            "agent_service_subnets": [
                {
                    "agent_service_subnet_is_active": False,
                    "agent_service_subnet_is_user_enabled": True,
                },
                {
                    "agent_service_subnet_is_active": True,
                    "agent_service_subnet_is_user_enabled": True,
                },
            ],
        },
        {
            "agent_service_name": "d",
            "agent_service_is_active": True,
            "agent_service_subnets": [
                {
                    "agent_service_subnet_is_active": True,
                    "agent_service_subnet_is_user_enabled": False,
                },
                {
                    "agent_service_subnet_is_active": True,
                    "agent_service_subnet_is_user_enabled": True,
                },
            ],
        },
        {
            "agent_service_name": "e",
            "agent_service_is_active": True,
            "agent_service_subnets": [
                {
                    "agent_service_subnet_is_active": False,
                    "agent_service_subnet_is_user_enabled": True,
                },
                {
                    "agent_service_subnet_is_active": False,
                    "agent_service_subnet_is_user_enabled": True,
                },
            ],
        },
        {
            "agent_service_name": "f",
            "agent_service_is_active": True,
            "agent_service_subnets": [
                {
                    "agent_service_subnet_is_active": False,
                    "agent_service_subnet_is_user_enabled": False,
                },
                {
                    "agent_service_subnet_is_active": False,
                    "agent_service_subnet_is_user_enabled": False,
                },
            ],
        },
        {
            "agent_service_name": "g",
            "agent_service_is_active": False,
            "agent_service_subnets": [
                {
                    "agent_service_subnet_is_active": False,
                    "agent_service_subnet_is_user_enabled": False,
                },
                {
                    "agent_service_subnet_is_active": False,
                    "agent_service_subnet_is_user_enabled": False,
                },
            ],
        },
    ]
    assert "a^^" in utils.collect_endpoint_services(agent_services)
    assert "b!^" in utils.collect_endpoint_services(agent_services)
    assert "c^~" in utils.collect_endpoint_services(agent_services)
    assert "d^~" in utils.collect_endpoint_services(agent_services)
    assert "e^!" in utils.collect_endpoint_services(agent_services)
    assert "f^!" in utils.collect_endpoint_services(agent_services)
    assert "g!!" in utils.collect_endpoint_services(agent_services)


def test_collect_connection_services():
    connection_services = {
        "agent_connection_subnets": [
            {
                "agent_connection_subnet_is_enabled": True,
                "agent_service_subnet_id": 1,
                "agent_connection_subnet_status": "OK",
            },
            {
                "agent_connection_subnet_is_enabled": True,
                "agent_service_subnet_id": 2,
                "agent_connection_subnet_status": "ERROR",
            },
            {
                "agent_connection_subnet_is_enabled": True,
                "agent_service_subnet_id": 6,
                "agent_connection_subnet_status": "something else",
            },
            {
                "agent_connection_subnet_is_enabled": True,
                "agent_service_subnet_id": 5,
                "agent_connection_subnet_status": "PENDING",
            },
            {
                "agent_connection_subnet_is_enabled": False,
                "agent_service_subnet_id": 8,
                "agent_connection_subnet_status": "PENDING",
            },
        ],
        "agent_1": {
            "agent_services": [
                {
                    "agent_service_subnet_id": 1,
                    "agent_service_name": "a",
                    "agent_service_subnets": [{"agent_service_subnet_id": 1}],
                },
                {
                    "agent_service_subnet_id": 2,
                    "agent_service_name": "b",
                    "agent_service_subnets": [{"agent_service_subnet_id": 2}],
                },
            ],
        },
        "agent_2": {
            "agent_services": [
                {
                    "agent_service_subnet_id": 4,
                    "agent_service_name": "d",
                    "agent_service_subnets": [{"agent_service_subnet_id": 4}],
                },
                {
                    "agent_service_subnet_id": 5,
                    "agent_service_name": "e",
                    "agent_service_subnets": [{"agent_service_subnet_id": 5}],
                },
                {
                    "agent_service_subnet_id": 6,
                    "agent_service_name": "f",
                    "agent_service_subnets": [{"agent_service_subnet_id": 6}],
                },
            ],
        },
    }
    assert "a^" in utils.collect_connection_services(connection_services)
    assert "b!" in utils.collect_connection_services(connection_services)
    assert "e~" in utils.collect_connection_services(connection_services)
    assert "f?" in utils.collect_connection_services(connection_services)


@pytest.mark.parametrize(
    "data,set_items,add_items,remove_items,clear_items,items",
    [
        [["b", "c"], [" abc "], [], [], False, ["abc"]],
        [["abcd", "b"], [], ["abcd"], [], False, ["abcd", "b"]],
        [["a", "b"], [], ["cdef"], [], False, ["a", "b", "cdef"]],
        [["a", "b"], [], [], ["a"], False, ["b"]],
        [["a", "b"], [], [], [], True, []],
    ],
)
def test_update_list(data, set_items, add_items, remove_items, clear_items, items):
    assert (
        utils.update_list(data, set_items, add_items, remove_items, clear_items)
        == items
    )


@pytest.mark.parametrize(
    "data,set_items,add_items,remove_items,clear_items",
    [
        [["b", "c"], ["ab"], [], [], False],
        [["b", "c"], ["a"], [], [], False],
        [["b", "c"], [""], [], [], False],
        [["b", "c"], ["    "], [], [], False],
        [["b", "c"], ["  a "], [], [], False],
    ],
)
def test_update_list__fail(data, set_items, add_items, remove_items, clear_items):
    with pytest.raises(SystemExit):
        utils.update_list(data, set_items, add_items, remove_items, clear_items)
