import functools
import os
import time

import click
import syntropy_sdk as sdk
from syntropy_sdk.exceptions import ApiException
from syntropy_sdk.utils import *


class EnvVars:
    API_URL = "SYNTROPY_API_SERVER"
    TOKEN = "SYNTROPY_API_TOKEN"


def syntropy_api(func):
    """Helper decorator that injects ApiClient instance into the arguments"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        API_URL = os.environ.get(EnvVars.API_URL)
        API_KEY = os.environ.get(EnvVars.TOKEN)

        if API_URL is None:
            click.secho(
                f"{EnvVars.API_URL} environment variable is missing.",
                err=True,
                fg="red",
            )
            raise SystemExit(1)

        config = sdk.Configuration()
        config.host = API_URL
        config.api_key["Authorization"] = API_KEY
        api = sdk.ApiClient(config)

        try:
            return func(*args, api=api, **kwargs)
        except ApiException as err:
            click.secho("API error occured", err=True, fg="red")
            click.secho(f"Reason: {str(err)}", err=True, fg="red")
            raise SystemExit(2)
        finally:
            del api

    return wrapper


def syntropy_platform(func):
    """Helper decorator that injects PlatformApi instance into the arguments"""

    @functools.wraps(func)
    def wrapper(*args, api=None, **kwargs):
        if os.environ.get(EnvVars.TOKEN) is None:
            click.secho(
                f"{EnvVars.TOKEN} environment variable is missing.",
                err=True,
                fg="yellow",
            )
        try:
            api = sdk.PlatformApi(api)
            return func(*args, platform=api, **kwargs)
        except:
            raise
        finally:
            del api

    return syntropy_api(wrapper)
