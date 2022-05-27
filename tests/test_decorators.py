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
    assert login_mock.call_count == 0
