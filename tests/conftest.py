import os
from unittest import mock

import pytest
import syntropy_sdk as sdk
from click.testing import CliRunner
from syntropy_sdk.rest import ApiException

from syntropycli import __main__ as ctl


@pytest.fixture
def env_mock():
    with mock.patch.dict(
        os.environ, {"SYNTROPY_API_SERVER": "server", "SYNTROPY_API_TOKEN": "token"}
    ) as the_mock:
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
