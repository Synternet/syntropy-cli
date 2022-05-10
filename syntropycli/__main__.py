#!/usr/bin/env python
from collections import defaultdict
from datetime import datetime, timedelta

import click
import syntropy_sdk as sdk
from syntropy_sdk import models

from syntropycli.decorators import *
from syntropycli.utils import *


@click.group()
def apis():
    """Syntropy Networks Command Line Interface."""


@apis.command()
@click.option("--skip", default=0, type=int, help="Skip N providers.")
@click.option("--take", default=128, type=int, help="Take N providers.")
@click.option(
    "--json",
    "-j",
    is_flag=True,
    default=False,
    help="Outputs a JSON instead of a table.",
)
@syntropy_api
def get_providers(skip, take, json, api):
    """Retrieve a list of endpoint providers."""
    api = sdk.AgentsApi(api)
    providers = WithPagination(api.v1_network_agents_providers_get)(
        skip=skip, take=take, _preload_content=False
    )["data"]
    fields = [
        ("ID", "agent_provider_id"),
        ("Name", "agent_provider_name"),
    ]
    print_table(providers, fields, to_json=json)


@apis.command()
@click.option("--skip", default=0, type=int, help="Skip N API keys.")
@click.option("--take", default=128, type=int, help="Take N API keys.")
@click.option(
    "--json",
    "-j",
    is_flag=True,
    default=False,
    help="Outputs a JSON instead of a table.",
)
@syntropy_api
def get_api_keys(skip, take, json, api):
    """List all API keys.

    API keys are being used by the endpoint agent to connect to the syntropy platform.

    By default this command will retrieve up to 128 API keys. You can use --take parameter to get more keys.
    """

    api = sdk.AuthApi(api)
    keys = WithPagination(api.v1_network_auth_api_keys_get)(
        skip=skip, take=take, _preload_content=False
    )["data"]

    fields = [
        ("ID", "api_key_id", lambda x: int(x)),
        ("Name", "api_key_name"),
        ("Is Suspended", "api_key_is_suspended", lambda x: x and "Yes" or "No"),
        ("Status", "api_key_status", lambda x: x and "Ok" or "Err"),
        ("Created At", "api_key_created_at"),
        ("Updated At", "api_key_updated_at"),
        ("Expires At", "api_key_valid_until"),
    ]
    print_table(keys, fields, to_json=json)


@apis.command()
@click.argument("name")
@click.argument("description")
@click.argument(
    "expires",
    type=click.DateTime(formats=["%Y-%m-%d %H:%M:%S"]),
    default=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S"),
)
@syntropy_api
def create_api_key(name, description, expires, api):
    """Create a API key for endpoint agent.

    NOTE: Be sure to remember the API key as it will be only available as a result of this command.
    """
    body = models.V1NetworkAuthApiKeysCreateRequest(
        api_key_name=name,
        api_key_valid_until=expires,
        api_key_description=description,
    )
    api = sdk.AuthApi(api)
    result = api.v1_network_auth_api_keys_create(body=body)
    click.echo(result.data.api_key_secret)


def confirm_deletion(name, id):
    try:
        return click.confirm(f"Do you want to delete '{name}' (id={id})?")
    except click.Abort:
        raise SystemExit(1)


@apis.command()
@click.option("--name", default=None, type=str)
@click.option("--id", default=None, type=int)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    default=False,
    help="Forces to delete all matching keys.",
)
@syntropy_api
def delete_api_key(name, id, yes, api):
    """Delete API key either by name or by id. If there are multiple names - please use id."""
    if name is None and id is None:
        click.secho("Either API key name or id must be specified.", err=True, fg="red")
        raise SystemExit(1)

    api = sdk.AuthApi(api)

    if id is None:
        keys = WithPagination(api.v1_network_auth_api_keys_get)(_preload_content=False)[
            "data"
        ]
        for key in keys:
            if key["api_key_name"] != name:
                continue
            if not yes and not confirm_deletion(key["api_key_name"], key["api_key_id"]):
                continue
            api.v1_network_auth_api_keys_delete(int(key["api_key_id"]))
            click.secho(
                f"Deleted API key: {key['api_key_name']} (id={key['api_key_id']}).",
                fg="green",
            )
    else:
        api.v1_network_auth_api_keys_delete(id)
        click.secho(f"Deleted API key: id={id}.", fg="green")


def _get_endpoints(
    name, id, tag, skip, take, show_services, online, offline, json, api
):
    if not name and not id and not tag and not online and not offline:
        agents = WithPagination(sdk.AgentsApi(api).v1_network_agents_get)(
            skip=skip,
            take=take,
            _preload_content=False,
        )["data"]
    else:
        filters = models.V1AgentFilter()
        if name:
            filters.agent_name = name
        elif id:
            filters.agent_id = [id]
        if tag:
            filters.agent_tag_name = [tag]

        if online:
            filters.agent_status = [models.AgentFilterAgentStatus.CONNECTED]
        elif offline:
            filters.agent_status = [
                models.AgentFilterAgentStatus.DISCONNECTED,
                models.AgentFilterAgentStatus.CONNECTED_WITH_ERRORS,
            ]

        agents = (
            sdk.AgentsApi(api)
            .v1_network_agents_search(
                models.V1NetworkAgentsSearchRequest(
                    filter=filters,
                    skip=skip,
                    take=take,
                ),
                # _preload_content=False,
            )
            .to_dict()["data"]
        )

    fields = [
        ("Agent ID", "agent_id"),
        ("Name", "agent_name"),
        ("Public IP", "agent_public_ipv4"),
        ("Provider", ("agent_provider", "agent_provider_name")),
        ("Location", "agent_location_city"),
        ("Online", "agent_is_online"),
        (
            "Tags",
            "agent_tags",
            lambda x: x and ", ".join(i["agent_tag_name"] for i in x) or "-",
        ),
    ]

    if show_services:
        ids = [agent["agent_id"] for agent in agents]
        agents_services = BatchedRequestFilter(
            sdk.AgentsApi(api).v1_network_agents_services_get,
            max_query_size=MAX_QUERY_FIELD_SIZE,
        )(filter=ids, _preload_content=False)["data"]
        agent_services = defaultdict(list)
        for agent in agents_services:
            agent_services[agent["agent_id"]].append(agent)
        agents = [
            {
                **agent,
                "agent_services": agent_services.get(agent["agent_id"], []),
            }
            for agent in agents
        ]
        fields.append(("Services", "agent_services", collect_endpoint_services))

    print_table(agents, fields, to_json=json)


@apis.command()
@click.option("--name", default=None, type=str, help="Filter endpoints by name.")
@click.option("--id", default=None, type=int, help="Filter endpoints by IDs.")
@click.option("--tag", default=None, type=str, help="Filter endpoints by tag.")
@click.option("--skip", default=0, type=int, help="Skip N endpoints.")
@click.option("--take", default=42, type=int, help="Take N endpoints.")
@click.option(
    "--show-services",
    is_flag=True,
    default=False,
    help="Retrieves services that are configured for each endpoint.",
)
@click.option(
    "--online", is_flag=True, default=False, help="List only online endpoints."
)
@click.option(
    "--offline", is_flag=True, default=False, help="List only offline endpoints."
)
@click.option(
    "--json",
    "-j",
    is_flag=True,
    default=False,
    help="Outputs a JSON instead of a table.",
)
@syntropy_api
def get_endpoints(name, id, tag, skip, take, show_services, online, offline, json, api):
    """List all endpoints.

    By default this command will retrieve up to 42 endpoints. You can use --take parameter to get more endpoints.

    Endpoint service status is added to the end of the service name with the following possible symbols:

    \b
    ^ - Enabled
    ! - Disabled
    ~ - Subnets partially enabled

    \b
    For example:
        `nginx^^` - the service is enabled as well as all subnets it exposes.
        `nginx^~` - the service is enabled, but only some subnets are enabled.
        `nginx!~` - the service is disabled, but some subnets are enabled.
        `nginx!!` - the service and subnets are disabled.

    """
    _get_endpoints(
        name,
        id,
        tag,
        skip,
        take,
        show_services,
        online,
        offline,
        json,
        api,
    )


@apis.command()
@click.argument("endpoint")
@click.option(
    "--name",
    "-n",
    is_flag=True,
    default=False,
    help="Use endpoint name instead of id.",
)
@click.option(
    "--json",
    "-j",
    is_flag=True,
    default=False,
    help="Outputs a JSON instead of a table.",
)
@click.option(
    "--set-provider",
    "-p",
    type=str,
    default=None,
    help="Set a provider to the endpoint.",
)
@click.option(
    "--set-tag",
    "-t",
    type=str,
    default=None,
    multiple=True,
    help="Set a tag to the endpoint(removes all other tags). Supports multiple options.",
)
@click.option(
    "--set-service",
    "-s",
    type=str,
    default=None,
    multiple=True,
    help="Enable a service for the endpoint(disables all other services). Supports multiple options.",
)
@click.option(
    "--add-tag",
    "-T",
    type=str,
    default=None,
    multiple=True,
    help="Add a tag to the endpoint(won't affect other tags). Supports multiple options.",
)
@click.option(
    "--enable-service",
    "-S",
    type=str,
    default=None,
    multiple=True,
    help="Enable a service for the endpoint(won't affect other services). Supports multiple options.",
)
@click.option(
    "--remove-tag",
    "-R",
    type=str,
    default=None,
    multiple=True,
    help="Remove a tag from the endpoint(won't affect other tags). Supports multiple options.",
)
@click.option("--clear-tags", is_flag=True, default=False, help="Removes all tags.")
@click.option(
    "--disable-service",
    "-D",
    type=str,
    default=None,
    multiple=True,
    help="Disable a service for the endpoint(won't affect other services). Supports multiple options.",
)
@click.option(
    "--disable-all-services", is_flag=True, default=False, help="Disable all services."
)
@click.option(
    "--enable-all-services", is_flag=True, default=False, help="Enable all services."
)
@click.option("--skip", default=0, type=int, help="Skip N endpoints.")
@click.option("--take", default=42, type=int, help="Take N endpoints.")
@syntropy_api
def configure_endpoints(
    api,
    endpoint,
    set_provider,
    set_tag,
    set_service,
    add_tag,
    enable_service,
    remove_tag,
    disable_service,
    clear_tags,
    disable_all_services,
    enable_all_services,
    name,
    take,
    skip,
    json,
):
    """Configures an endpoint with provided provider, tags. Also, allows to enable/disable services.
    Endpoint can be an ID or a name (use -n option). Multiple endpoints can be configured if names match partially with the provided name.

    It is possible to supply multiple --set-tag, --add-tag and --remove-tag options. The sequence of operations is set, add and then remove.
    So if you run this:

        syntropyctl configure-endpoints --set-tag tag1 --set-tag tag2 --add-tag tag3 --add-tag tag4 --remove-tag tag1 -n <endpoint-name>

    \b
    then syntropyctl will:
        1. clear all tags and add tag1 and tag2,
        2. add tag3 and tag4,
        3. remove tag1.

    The same applies to services.
    """
    body = models.V1NetworkAgentsSearchRequest(
        filter=models.V1AgentFilter(agent_name=endpoint)
        if name
        else models.V1AgentFilter(agent_id=endpoint)
    )
    agents = (
        sdk.AgentsApi(api)
        .v1_network_agents_search(
            body,
        )
        .to_dict()["data"]
    )

    if not agents:
        click.secho("Could not find any endpoints.", err=True, fg="red")
        raise SystemExit(1)
    else:
        click.secho(f"Found {len(agents)} endpoints.", fg="green")

    if set_provider or set_tag or add_tag or remove_tag or clear_tags:
        agents_tags = {
            agent["agent_id"]: [
                tag["agent_tag_name"] for tag in agent.get("agent_tags", []) if tag
            ]
            for agent in agents
            if "agent_tags" in agent
        }
        for agent in agents:
            original_tags = agents_tags.get(agent["agent_id"], [])
            tags = update_list(original_tags, set_tag, add_tag, remove_tag, clear_tags)
            payload = {}
            current_provider = (
                agent.get("agent_provider") if agent.get("agent_provider") else {}
            )
            if set_provider and set_provider != current_provider.get(
                "agent_provider_name"
            ):
                payload["agent_provider_name"] = set_provider
            if (set_tag or add_tag or remove_tag or clear_tags) and set(
                original_tags
            ) != set(tags):
                payload["agent_tags"] = tags
            if payload:
                sdk.AgentsApi(api).v1_network_agents_update(payload, agent["agent_id"])
                click.secho("Tags and provider configured.", fg="green")
            else:
                click.secho(
                    "Nothing to do for tags and provider configuration.", fg="yellow"
                )

    show_services = False
    if (
        set_service
        or enable_service
        or disable_service
        or enable_all_services
        or disable_all_services
    ):
        show_services = True
        ids = [agent["agent_id"] for agent in agents]
        agents_services_all = sdk.utils.BatchedRequestFilter(
            sdk.AgentsApi(api).v1_network_agents_services_get,
            max_query_size=MAX_QUERY_FIELD_SIZE,
        )(filter=ids, _preload_content=False)["data"]

        agents_services = defaultdict(list)
        for agent in agents_services_all:
            agents_services[agent["agent_id"]].append(agent)
        for agent in agents:
            services = {
                service["agent_service_name"]: service
                for service in agents_services[agent["agent_id"]]
            }
            enabled_services = [
                service["agent_service_name"]
                for service in agents_services[agent["agent_id"]]
                if (
                    (
                        all(
                            subnet["agent_service_subnet_is_user_enabled"]
                            for subnet in service["agent_service_subnets"]
                        )
                        and service["agent_service_is_active"]
                    )
                    or enable_all_services
                )
            ]
            enabled_services = update_list(
                enabled_services,
                set_service,
                enable_service,
                disable_service,
                disable_all_services,
                validate=False,
            )
            missing_services = [
                service for service in enabled_services if service not in services
            ]
            if missing_services:
                click.secho(
                    f"Warning: the following services were not found: {', '.join(missing_services)}",
                    err=True,
                    fg="yellow",
                )
            subnets = [
                models.V1NetworkAgentsServicesUpdateRequestSubnetsToUpdate(
                    is_enabled=name in enabled_services,
                    agent_service_subnet_id=subnet["agent_service_subnet_id"],
                )
                for name, service in services.items()
                for subnet in service["agent_service_subnets"]
                if subnet["agent_service_subnet_is_user_enabled"]
                != (name in enabled_services)
            ]
            if subnets:
                payload = models.V1NetworkAgentsServicesUpdateRequest(
                    subnets_to_update=subnets
                )
                sdk.AgentsApi(api).v1_network_agents_services_update(payload)
                click.secho("Service subnets updated.", fg="green")
            else:
                click.secho("Nothing to do for service configuration.", fg="yellow")

    name_param, id_param = None, None
    if name:
        name_param = endpoint
    else:
        id_param = endpoint

    _get_endpoints(
        name_param,
        id_param,
        None,
        skip,
        take,
        show_services,
        None,
        None,
        json,
        api,
    )


@apis.command()
@click.option("--id", default=None, type=int, help="Filter endpoints by ID.")
@click.option("--name", default=None, type=str, help="Filter endpoints by ID or name.")
@click.option("--skip", default=0, type=int, help="Skip N connections.")
@click.option("--take", default=42, type=int, help="Take N connections.")
@click.option(
    "--show-services",
    is_flag=True,
    default=False,
    help="Retrieves services that are configured for each endpoint.",
)
@click.option(
    "--json",
    "-j",
    is_flag=True,
    default=False,
    help="Outputs a JSON instead of a table.",
)
@syntropy_api
def get_connections(id, name, skip, take, show_services, json, api):
    """Retrieves connections.

    Connection service status is added to the end of the service name with the following possible symbols:

    \b
    ^ - Service is online.
    ! - There was an error exposing the service
    ~ - Service is in PENDING state
    ? - Unknown state

    By default this command will retrieve up to 42 connections. You can use --take parameter to get more connections.
    """
    if name or id:
        if name:
            agents = (
                sdk.AgentsApi(api)
                .v1_network_agents_search(
                    models.V1NetworkAgentsSearchRequest(
                        filter=models.V1AgentFilter(agent_name=name)
                    ),
                )
                .to_dict()["data"]
            )
            id = [agent["agent_id"] for agent in agents]
        else:
            id = [int(id)]

        filters = models.V1ConnectionFilter(agent_id=id)

        connections = (
            sdk.ConnectionsApi(api)
            .v1_network_connections_search(
                body=models.V1NetworkConnectionsSearchRequest(
                    filter=filters,
                    skip=skip,
                    take=take,
                ),
            )
            .to_dict()["data"]
        )
    else:
        connections = WithPagination(
            sdk.ConnectionsApi(api).v1_network_connections_get
        )(skip=skip, take=take, _preload_content=False,)["data"]

    fields = [
        ("ID", "agent_connection_group_id"),
        ("Endpoint 1", ("agent_1", "agent_name")),
        ("ID 1", ("agent_1", "agent_id")),
        ("IP 1", ("agent_1", "agent_public_ipv4")),
        ("Endpoint 2", ("agent_2", "agent_name")),
        ("ID 2", ("agent_2", "agent_id")),
        ("IP 2", ("agent_2", "agent_public_ipv4")),
        ("Status", "agent_connection_group_status"),
        ("Modified At", "agent_connection_group_updated_at"),
        ("Latency", "agent_connection_latency_ms"),
        ("Packet Loss", "agent_connection_packet_loss"),
    ]

    if show_services:
        ids = [connection["agent_connection_group_id"] for connection in connections]
        connections_services = BatchedRequestFilter(
            sdk.ConnectionsApi(api).v1_network_connections_services_get,
            max_query_size=MAX_QUERY_FIELD_SIZE,
        )(filter=ids, _preload_content=False)["data"]
        connection_services = {
            connection["agent_connection_group_id"]: connection
            for connection in connections_services
        }
        connections = [
            {
                **connection,
                "agent_connection_services": connection_services[
                    connection["agent_connection_group_id"]
                ],
            }
            for connection in connections
        ]
        fields.append(
            ("Services", "agent_connection_services", collect_connection_services)
        )

    print_table(connections, fields, to_json=json)


@apis.command()
@click.argument("agents", nargs=-1)
@click.option(
    "--use-names",
    is_flag=True,
    default=False,
    help="Use endpoint names instead of ids. Will not work with name duplicates.",
)
@click.option(
    "--json",
    "-j",
    is_flag=True,
    default=False,
    help="Outputs a JSON instead of a table.",
)
@syntropy_api
def create_connections(agents, use_names, json, api):
    """Create connections between endpoints. Number of endpoints must be even.

    \b
    Arguments:
        agents - a list of endpoint ids or names separated by spaces.

    In order to use endpoint names instead of ids provide --use-names option.

    Example:

        syntropyctl create-connections 1 2 3 4 5 6 7 8

        This command will create 4 connections from Endpoint 1 to Endpoint 2 like this:

        \b
        Endpoint 1 ID | Endpoint 2 ID
        1             | 2
        3             | 4
        5             | 6
        7             | 8
    """

    if use_names:
        all_agents = WithPagination(sdk.AgentsApi(api).v1_network_agents_get)(
            _preload_content=False
        )["data"]
        agents = find_by_name(all_agents, agents, "agent")
        if any(i is None for i in agents):
            raise SystemExit(1)
    else:
        try:
            agents = [int(i) for i in agents]
        except ValueError:
            click.secho("Invalid agent id", err=True, fg="red")
            raise SystemExit(1)

    if len(agents) == 0 or len(agents) % 2 != 0:
        click.secho("Number of agents must be even.", err=True, fg="red")
        raise SystemExit(1)
    agents = list(zip(agents[:-1:2], agents[1::2]))

    body = models.V1NetworkConnectionsCreateP2PRequest(
        agent_pairs=[
            models.V1NetworkConnectionsCreateP2PRequestAgentPairs(
                agent_1_id=a,
                agent_2_id=b,
            )
            for a, b in agents
        ],
    )
    result = sdk.ConnectionsApi(api).v1_network_connections_create_p2_p(
        body=body, _preload_content=False
    )

    if result and "errors" in result:
        for error in result["errors"]:
            click.secho(f"Error: {error.get('message')}", err=True, fg="red")


@apis.command()
@click.argument("ids", type=int, nargs=-1)
@syntropy_api
def delete_connection(ids, api):
    """Delete connections using their ID."""
    for id in ids:
        sdk.ConnectionsApi(api).v1_network_connections_delete(id)


def main():
    apis(prog_name="syntropyctl")


if __name__ == "__main__":
    main()
