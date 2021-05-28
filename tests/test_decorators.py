from unittest import mock

import pytest
import syntropy_sdk as sdk
from syntropy_sdk.rest import ApiException

from syntropycli import decorators
from syntropycli.decorators import *


def test_syntropy_api(env_mock, login_mock):
    func = mock.Mock(return_value="ret")
    decorated = syntropy_api(func)
    assert decorated("arg", kw="kwarg") == "ret"
    func.assert_called_once_with("arg", kw="kwarg", api=mock.ANY)
    login_mock.assert_called_once()


def test_syntropy_platform(env_mock, login_mock):
    func = mock.Mock(return_value="ret")
    decorated = syntropy_platform(func)
    assert decorated("arg", kw="kwarg") == "ret"
    func.assert_called_once_with("arg", kw="kwarg", platform=mock.ANY)
    login_mock.assert_called_once()


def test_syntropy_platform__fail(env_mock, login_mock):
    func = mock.Mock(side_effect=ValueError)
    decorated = syntropy_platform(func)
    with pytest.raises(ValueError):
        decorated("arg", kw="kwarg")
    login_mock.assert_called_once()


def test_syntropy_platform__api_fail(env_mock, login_mock):
    func = mock.Mock(side_effect=ApiException)
    decorated = syntropy_platform(func)
    with pytest.raises(SystemExit) as err:
        decorated("arg", kw="kwarg")
    assert err.value.code == 2
    login_mock.assert_called_once()
