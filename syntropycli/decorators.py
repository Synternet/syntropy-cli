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

        if API_KEY is None:
            click.secho(
                f"{EnvVars.API_KEY} environment variable is missing.",
                err=True,
                fg="red",
            )
            raise SystemExit(1)

        try:
            config = sdk.Configuration()
            config.host = API_URL
            config.api_key[
                "Authorization"
            ] = "Bearer " + sdk.utils.login_with_access_token(API_URL, API_KEY)
            api = sdk.ApiClient(config)

            return func(*args, api=api, **kwargs)
        except ApiException as err:
            click.secho("API error occured", err=True, fg="red")
            click.secho(f"Reason: {str(err)}", err=True, fg="red")
            raise SystemExit(2)

    return wrapper
