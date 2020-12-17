#!/usr/bin/env python
from collections import defaultdict
from datetime import datetime, timedelta

import click
import syntropy_sdk as sdk

from syntropycli.decorators import *
from syntropycli.utils import *


@click.group()
def apis():
    """Syntropy Networks cli tool"""


@apis.command()
@click.argument("username")
@click.argument("password", default=None, required=False)
@syntropy_api
def login(username, password, api):
    """Login with username and password.

    Will retrieve access token and print it to stdout. You can provide the password as a second parameter
    or type it when prompted if the password is not provided.

    \b
    Example:
        syntropyctl login MyUser@example.com MyPassword

        \b
        syntropyctl login MyUser@example.com
        Password: <type your password here>
    """
    if not password:
        password = click.prompt("Password", default=None, hide_input=True)

    if password is None:
        click.secho("Password must be provided", err=True, fg="red")
        raise SystemExit(1)

    payload = {"user_email": username, "user_password": password, "additionalProp1": {}}
    api = sdk.AuthApi(api)
    try:
        token = api.local(body=payload)
        click.echo(token["refresh_token"])
    except ApiException as err:
        click.secho("Login was not successful", err=True, fg="red")
        click.secho(f"Reason: {str(err)}", err=True, fg="red")
        raise SystemExit(1)


@apis.command()
@click.option("--skip", default=0, type=int, help="Skip N providers")
@click.option("--take", default=128, type=int, help="Take N providers")
@click.option(
    "--json",
    "-j",
    is_flag=True,
    default=False,
    help="Outputs a JSON instead of a table",
)
@syntropy_api
def get_providers(skip, take, json, api):
    """Retrieve a list of providers."""
    provider = sdk.ProvidersApi(api)
    providers = provider.index(skip=skip, take=take)
    fields = [
        ("ID", "provider_id"),
        ("Name", "provider_name"),
        ("Created At", "provider_created_at"),
        ("Updated At", "provider_updated_at"),
    ]
    print_table(providers, fields, to_json=json)


@apis.command()
@click.option(
    "--show-secret", "-s", is_flag=True, default=False, help="Shows API secrets"
)
@click.option("--skip", default=0, type=int, help="Skip N API keys")
@click.option("--take", default=128, type=int, help="Take N API keys")
@click.option(
    "--json",
    "-j",
    is_flag=True,
    default=False,
    help="Outputs a JSON instead of a table",
)
@syntropy_platform
def get_api_keys(show_secret, skip, take, json, platform):
    """List all API keys.

    API keys are being used by the endpoint agent to connect to the syntropy platform.

    By default this command will retrieve up to 128 API keys. You can use --take parameter to get more keys.
    """
    keys = platform.index_api_key(skip=skip, take=take)["data"]

    fields = [
        ("ID", "api_key_id"),
        ("User ID", "user_id"),
        ("Key ID", "api_key_id"),
        ("Key Name", "api_key_name"),
        ("Is Suspended", "api_key_is_suspended", lambda x: x and "Yes" or "No"),
        ("Status", "api_key_status", lambda x: x and "Ok" or "Err"),
        ("Secret", "api_key_secret", lambda x: show_secret and x or "-"),
        ("Created At", "api_key_created_at"),
        ("Updated At", "api_key_updated_at"),
        ("Expires At", "api_key_valid_until"),
    ]
    print_table(keys, fields, to_json=json)


@apis.command()
@click.argument("name")
@click.argument(
    "expires",
    type=click.DateTime(formats=["%Y-%m-%d %H:%M:%S"]),
    default=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S"),
)
@click.option("--suspended", "-s", is_flag=True, help="Create a suspended API key")
@syntropy_platform
def create_api_key(name, suspended, expires, platform):
    """Create a API key."""
    body = {
        "api_key_name": name,
        "api_key_is_suspended": suspended,
        "api_key_valid_until": expires,
    }
    result = platform.create_api_key(body=body)
    click.echo(result["data"]["api_key_id"])


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
    help="Forces to delete all matching networks.",
)
@syntropy_platform
def delete_api_key(name, id, yes, platform):
    """Delete API key either by name or by id. If there are multiple names - please use id."""
    if name is None and id is None:
        click.secho("Either API key name or id must be specified.", err=True, fg="red")
        raise SystemExit(1)

    if id is None:
        keys = platform.index_api_key(filter=f"api_key_name:{name}")["data"]
        for key in keys:
            if not yes and not confirm_deletion(key["api_key_name"], key["api_key_id"]):
                continue

            platform.delete_api_key(key["api_key_id"])
            click.secho(
                f"Deleted API key: {key['api_key_name']} (id={key['api_key_id']}).",
                fg="green",
            )
    else:
        platform.delete_api_key(id)
        click.secho(f"Deleted API key: id={id}.", fg="green")


def _get_endpoints(
    name, id, tag, network, skip, take, show_services, online, offline, json, platform
):
    filters = []
    if name:
        filters.append(f"id|name:{name}")
    elif id:
        filters.append(f"ids[]:{id}")
    if tag:
        filters.append(f"tags_names[]:{tag}")
    if network:
        filters.append(f"networks_names[]:{network}")
    agents = platform.index_agents(
        filter=",".join(filters) if filters else None, skip=skip, take=take
    )["data"]

    if online or offline:
        filtered_agents = []
        is_online = online and not offline
        while agents and len(filtered_agents) < take:
            filtered_agents += [
                agent for agent in agents if agent["agent_is_online"] == is_online
            ]
            if len(filtered_agents) < take:
                skip += take
                agents = platform.index_agents(
                    filter=",".join(filters) if filters else None, skip=skip, take=take
                )["data"]
        agents = filtered_agents

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
        agents_services = BatchedRequest(
            platform.get_agent_services_with_subnets,
            max_payload_size=MAX_QUERY_FIELD_SIZE,
        )(ids)["data"]
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
@click.option("--name", default=None, type=str, help="Filter endpoints by name")
@click.option("--id", default=None, type=int, help="Filter endpoints by IDs")
@click.option(
    "--network", default=None, type=str, help="Filter endpoints by network name"
)
@click.option("--tag", default=None, type=str, help="Filter endpoints by tag")
@click.option("--skip", default=0, type=int, help="Skip N endpoints")
@click.option("--take", default=42, type=int, help="Take N endpoints")
@click.option(
    "--show-services",
    is_flag=True,
    default=False,
    help="Retrieves services that are configured for each endpoint",
)
@click.option(
    "--online", is_flag=True, default=False, help="List only online endpoints"
)
@click.option(
    "--offline", is_flag=True, default=False, help="List only offline endpoints"
)
@click.option(
    "--json",
    "-j",
    is_flag=True,
    default=False,
    help="Outputs a JSON instead of a table",
)
@syntropy_platform
def get_endpoints(
    name, id, tag, network, skip, take, show_services, online, offline, json, platform
):
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
        network,
        skip,
        take,
        show_services,
        online,
        offline,
        json,
        platform,
    )


@apis.command()
@click.argument("endpoint")
@click.option(
    "--json",
    "-j",
    is_flag=True,
    default=False,
    help="Outputs a JSON instead of a table",
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
@click.option("--clear-tags", is_flag=True, default=False, help="Removes all tags")
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
@click.option("--skip", default=0, type=int, help="Skip N endpoints")
@click.option("--take", default=42, type=int, help="Take N endpoints")
@syntropy_platform
def configure_endpoints(
    platform,
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
    take,
    skip,
    json,
):
    """Configures an endpoint with provided provider, tags. Also, allows to enable/disable services.
    Endpoint can be an ID or a name. Multiple endpoints can be configured if names match partially with the provided name.

    It is possible to supply multiple --set-tag, --add-tag and --remove-tag options. The sequence of operations is set, add and then remove.
    So if you run this:

        syntropyctl endpoint-name --set-tag tag1 --set-tag tag2 --add-tag tag3 --add-tag4 --remove-tag tag1

    \b
    then syntropyctl will:
        1. clear all tags and add tag1 and tag2
        2. add tag3 and tag4
        3. remove tag1

    The same applies to services.
    """
    agents = platform.index_agents(
        filter=f"id|name:{endpoint}",
    )["data"]

    if not agents:
        click.secho("Could not find any endpoints.", err=True, fg="red")
        raise SystemExit(1)
    else:
        click.secho(f"Found {len(agents)} endpoints.", fg="green")

    if set_provider or set_tag or add_tag or remove_tag or clear_tags:
        agents_tags = {
            agent["agent_id"]: [
                tag["agent_tag_name"] for tag in agent.get("agent_tags", [])
            ]
            for agent in agents
            if "agent_tags" in agent
        }
        for agent in agents:
            original_tags = agents_tags.get(agent["agent_id"], [])
            tags = _update_list(original_tags, set_tag, add_tag, remove_tag, clear_tags)
            payload = {}
            if set_provider and set_provider != agent.get("agent_provider", {}).get(
                "agent_provider_name"
            ):
                payload["agent_provider_name"] = set_provider
            if (set_tag or add_tag or remove_tag or clear_tags) and set(
                original_tags
            ) != set(tags):
                payload["agent_tags"] = tags
            if payload:
                platform.patch_agents(payload, agent["agent_id"])
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
        agents_services_all = BatchedRequest(
            platform.get_agent_services_with_subnets,
            max_payload_size=MAX_QUERY_FIELD_SIZE,
        )(ids)["data"]
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
            enabled_services = _update_list(
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
                {
                    "id": subnet["agent_service_subnet_id"],
                    "isEnabled": name in enabled_services,
                }
                for name, service in services.items()
                for subnet in service["agent_service_subnets"]
                if subnet["agent_service_subnet_is_user_enabled"]
                != (name in enabled_services)
            ]
            if subnets:
                payload = {"subnetsToUpdate": subnets}
                platform.update_agent_services_subnets_status(payload)
                click.secho("Service subnets updated.", fg="green")
            else:
                click.secho("Nothing to do for service configuration.", fg="yellow")

    _get_endpoints(
        endpoint,
        None,
        None,
        None,
        skip,
        take,
        show_services,
        None,
        None,
        json,
        platform,
    )


@apis.command()
@click.option(
    "--json",
    "-j",
    is_flag=True,
    default=False,
    help="Outputs a JSON instead of a table",
)
@syntropy_platform
def get_topology(json, platform):
    """Retrieves networks topology."""
    topology = platform.topology_networks()["data"]

    fields = [
        ("Network name", "network_name"),
        ("Network type", "network_type"),
        ("Network ID", "network_id"),
        ("Gateway ID", "agent_gateway_id"),
        ("N# of endpoints", "network_agents_count"),
        ("N# of connections", "network_agent_connections_count"),
    ]
    print_table(topology, fields, to_json=json)


@apis.command()
@click.option(
    "--network", default=None, type=str, help="Filter connections by network name or ID"
)
@click.option("--id", default=None, type=int, help="Filter endpoints by ID")
@click.option("--skip", default=0, type=int, help="Skip N connections")
@click.option("--take", default=42, type=int, help="Take N connections")
@click.option(
    "--show-services",
    is_flag=True,
    default=False,
    help="Retrieves services that are configured for each endpoint",
)
@click.option(
    "--json",
    "-j",
    is_flag=True,
    default=False,
    help="Outputs a JSON instead of a table",
)
@syntropy_platform
def get_connections(network, id, skip, take, show_services, json, platform):
    """Retrieves network connections.

    Connection service status is added to the end of the service name with the following possible symbols:

    \b
    ^ - Connection is online.
    ! - There was an error establishing the connection
    # - Connection is offline
    * - Connection is in warning state
    ~ - Connection is being established
    ? - Unknown state

    By default this command will retrieve up to 42 connections. You can use --take parameter to get more connections.
    """
    filters = []
    if network:
        try:
            filters.append(f"networks[]:{int(network)}")
        except ValueError:
            networks = platform.index_networks(filter=f"id|name:{network}")["data"]
            filters.append(
                f"networks[]:{','.join(str(net['network_id']) for net in networks)}"
            )

    if id:
        filters.append(f"id|name:{id}")
    connections = platform.index_connections(
        filter=",".join(filters) if filters else None,
        skip=skip,
        take=take,
    )["data"]
    fields = [
        ("ID", "agent_connection_id"),
        ("Endpoint 1", ("agent_1", "agent_name")),
        ("IP 1", ("agent_1", "agent_public_ipv4")),
        ("Endpoint 2", ("agent_2", "agent_name")),
        ("IP 2", ("agent_2", "agent_public_ipv4")),
        ("Status", "agent_connection_status"),
        ("Network name", "network_name"),
        ("Network type", "network_type"),
        ("Network ID", ("network", "network_id")),
        ("Gateway ID", "agent_gateway_id"),
        ("Created At", "agent_connection_created_at"),
        ("Modified At", "agent_connection_modified_at"),
        ("SDN Policy ID", "agent_sdn_policy_id"),
        ("Link Tag", "agent_connection_link_tag"),
        ("Last Handshake", "agent_connection_last_handshake"),
        ("TX total", "agent_connection_tx_bytes_total"),
        ("RX total", "agent_connection_rx_bytes_total"),
        ("Latency", "agent_connection_latency_ms"),
        ("Packet Loss", "agent_connection_packet_loss"),
    ]

    if show_services:
        ids = [connection["agent_connection_id"] for connection in connections]
        connections_services = BatchedRequest(
            platform.get_connection_services, max_payload_size=MAX_QUERY_FIELD_SIZE
        )(ids)["data"]
        connection_services = {
            connection["agent_connection_id"]: connection
            for connection in connections_services
        }
        connections = [
            {
                **connection,
                "agent_connection_services": connection_services[
                    connection["agent_connection_id"]
                ],
            }
            for connection in connections
        ]
        fields.append(
            ("Services", "agent_connection_services", collect_connection_services)
        )

    print_table(connections, fields, to_json=json)


@apis.command()
@click.argument("network")
@click.argument("agents", nargs=-1)
@click.option(
    "--use-names",
    is_flag=True,
    default=False,
    help="Use network and endpoint names instead of ids. Will not work with name duplicates.",
)
@click.option(
    "--json",
    "-j",
    is_flag=True,
    default=False,
    help="Outputs a JSON instead of a table",
)
@syntropy_platform
def create_connections(network, agents, use_names, json, platform):
    """Create connections between endpoints. Number of endpoints must be even.

    \b
    Arguments:
        network - either a network name or ID
        agents - a list of endpoint ids or names separated by spaces

    In order to use endpoint names instead of ids provide --use-names option.

    Example:

        syntropyctl create-connections MyNetworkName 1 2 3 4 5 6 7 8

        This command will create 4 connections from Endpoint 1 to Endpoint 2 like this:

        \b
        Endpoint 1 ID | Endpoint 2 ID
        1             | 2
        3             | 4
        5             | 6
        7             | 8
    """

    networks = platform.index_networks(filter=f"id|name:{network}")["data"]
    if len(networks) != 1:
        click.secho(f"Could not find the network {network}", err=True, fg="red")
        raise SystemExit(1)

    network = networks[0]["network_id"]
    network_type = networks[0]["network_type"]
    if use_names:
        all_agents = platform.index_agents(take=TAKE_MAX_ITEMS_PER_CALL)["data"]
        agents = find_by_name(all_agents, agents, "agent")
        if any(i is None for i in agents):
            raise SystemExit(1)
    else:
        try:
            agents = [int(i) for i in agents]
        except ValueError:
            click.secho("Invalid agent id", err=True, fg="red")
            raise SystemExit(1)

    if network_type == sdk.NetworkType.POINT_TO_POINT:
        if len(agents) == 0 or len(agents) % 2 != 0:
            click.secho("Number of agents must be even.", err=True, fg="red")
            raise SystemExit(1)
        agents = list(zip(agents[:-1:2], agents[1::2]))

    body = {
        "network_id": network,
        "agent_ids": agents,
        "network_update_by": sdk.NetworkGenesisType.SDK,
    }
    connections = platform.create_connections(body=body)["data"]

    fields = [
        ("Connection ID", "agent_connection_id"),
        ("Endpoint 1 ID", "agent_1_id"),
        ("Endpoint 1 WG", "agent_wg_1_id"),
        ("Endpoint 2 ID", "agent_2_id"),
        ("Endpoint 2 WG", "agent_wg_2_id"),
        ("Network ID", "network_id"),
    ]
    print_table(connections, fields, to_json=json)


@apis.command()
@click.argument("id", type=int)
@syntropy_platform
def delete_connection(id, platform):
    """Delete a connection."""
    platform.delete_connection(id)


@apis.command()
@click.option("--network", default=None, type=str, help="Filter networks by name/ID")
@click.option(
    "--show-secret", "-s", is_flag=True, default=False, help="Shows Network secrets"
)
@click.option("--skip", default=0, type=int, help="Skip N networks")
@click.option("--take", default=42, type=int, help="Take N networks")
@click.option(
    "--json",
    "-j",
    is_flag=True,
    default=False,
    help="Outputs a JSON instead of a table",
)
@syntropy_platform
def get_networks(network, show_secret, skip, take, json, platform):
    """List all networks.

    By default this command will retrieve up to 42 networks. You can use --take parameter to get more networks.
    """
    networks = platform.index_networks(
        filter=f"id|name:{network}" if network else None,
        skip=skip,
        take=take,
    )["data"]

    fields = [
        ("Organization ID", "organization_id"),
        ("User ID", "user_id"),
        ("Agent Gateway ID", "agent_gateway_id"),
        ("Network ID", "network_id"),
        ("Network Name", "network_name"),
        ("Network Type", "network_type"),
        ("Network Topology", ("network_metadata", "network_type")),
        ("Network Secret", "network_key", lambda x: show_secret and x or "-"),
        (
            "SDN Connections",
            "network_disable_sdn_connections",
            lambda x: x and "Disabled" or "Enabled",
        ),
        ("Created At", "network_created_at"),
        ("Updated At", "network_updated_at"),
        ("Created By", ("network_metadata", "network_created_by")),
        ("Updated By", ("network_metadata", "network_updated_by")),
    ]
    print_table(networks, fields, to_json=json)


@apis.command()
@click.argument("name")
@click.option(
    "--network-type",
    default=sdk.NetworkType.POINT_TO_POINT,
    help="Low level network type.",
    hidden=True,
)
@click.option(
    "--gateway-id",
    default=0,
    type=int,
    help="Endpoint ID to use as gateway for GATEWAY network type.",
    hidden=True,
)
@click.option(
    "--topology",
    default=sdk.MetadataNetworkType.P2P,
    help="Specifies Network Topology that is used by configure-networks or Ansible playbooks.",
)
@click.option(
    "--disable-sdn-connections",
    is_flag=True,
    default=True,
    help="Disable SDN connections. Default is disable.",
    hidden=True,
)
@syntropy_platform
def create_network(
    name, network_type, topology, gateway_id, disable_sdn_connections, platform
):
    """Create a network.

    Possible network topologies are P2P, P2M, MESH. The network topology is mainly used for
    Network as Code usage scenarious.

    \b
    P2P - used to configure the network using endpoint pairs.
    P2M - used to configure the network when one endpoint connects to many endpoints.
    MESH - used to configure the network where every endpoint is connected to every other endpoint.

    \b
    Examples:
        # Create a network with P2P topology
        syntropyctl create-network MyNetworkName

    \b
        # Create a network with MESH topology
        syntropyctl create-network MyNetworkName --topology MESH

    """
    if network_type not in ALLOWED_NETWORK_TYPES:
        click.secho(f"Network type {network_type} is not allowed.", err=True, fg="red")
        raise SystemExit(1)

    topology = topology.upper() if topology else topology
    if topology is not None and topology not in ALLOWED_NETWORK_TOPOLOGIES:
        click.secho(f"Network topology {topology} is not allowed.", err=True, fg="red")
        raise SystemExit(1)

    body = {
        "network_name": name,
        "network_type": network_type,
        "agent_gateway_id": gateway_id,
        "network_disable_sdn_connections": disable_sdn_connections,
        "network_metadata": {
            "network_created_by": sdk.NetworkGenesisType.SDK,
            "network_type": topology,
        },
    }
    result = platform.create_network(body=body)
    click.echo(result["data"]["network_id"])


@apis.command()
@click.argument("network")
@click.option(
    "--add-endpoint",
    "-a",
    multiple=True,
    help="Add an endpoint to the network. Supports multiple options.",
)
@click.option(
    "--remove-endpoint",
    "-r",
    multiple=True,
    help="Remove an endpoint from the network. Supports multiple options.",
)
@click.option(
    "--use-names",
    is_flag=True,
    default=False,
    help="Use endpoint names instead of ids. Will not work with name duplicates.",
)
@click.option("--skip", default=0, type=int, help="Skip N networks")
@click.option("--take", default=42, type=int, help="Take N networks")
@click.option(
    "--json",
    "-j",
    is_flag=True,
    default=False,
    help="Outputs a JSON instead of a table",
)
@syntropy_platform
def manage_network_endpoints(
    network, add_endpoint, remove_endpoint, use_names, skip, take, json, platform
):
    """Add/Remove endpoints to/from a network.

    This command first removes and then adds endpoints if -r and -a are used together.
    It is possible to add/remove endpoints for multiple networks if they share the same name, for example:

        syntropyctl manage-network-endpoints My-Network-

    will match `My-Network-DNS`, `My-Network-Test`, `Another-My-Network` and so on.

    You can check what networks match by running manage-network-endpoints command without any -r or -a options.
    This will also print already existing endpoints for each network.
    """
    networks = platform.index_networks(
        filter=f"id|name:{network}" if network else None,
        skip=skip,
        take=take,
    )["data"]
    if not networks:
        click.secho(
            f"Could not find a network by id/name {network}.", err=True, fg="red"
        )
        raise SystemExit(1)
    else:
        click.secho(f"Found {len(networks)} networks.", fg="green")

    resolved_agents = [
        [
            agent["agent_id"]
            for agent in WithRetry(platform.index_agents)(
                filter=f"name:{endpoint}" if use_names else f"ids[]:{endpoint}",
                load_relations=False,
            )["data"]
        ]
        for endpoint in add_endpoint
    ]

    add_agents = []
    for endpoint, agent in zip(add_endpoint, resolved_agents):
        if len(agent) == 0:
            click.secho(f"Endpoint {endpoint} could not be found.")
            raise SystemExit(1)
        elif len(agent) != 1:
            click.secho(
                f"Multiple endpoints found for {endpoint}: {','.join(str(i) for i in agent)}"
            )
            raise SystemExit(1)
        add_agents += agent

    networks_info = [
        platform.get_network_info(net["network_id"])["data"] for net in networks
    ]

    if remove_endpoint:
        for network in networks_info:
            agents = [
                agent["agent"]["agent_id"]
                for agent in network["network_agents"]
                if (
                    str(agent["agent"]["agent_id"]) in remove_endpoint and not use_names
                )
                or (agent["agent"]["agent_name"] in remove_endpoint and use_names)
            ]
            if agents:
                platform.remove_network_agents(agents, network["network"]["network_id"])
                click.secho(
                    f"Removed {len(agents)} endpoints from network {network['network']['network_name']}.",
                    fg="yellow",
                )

    if add_agents:
        for network in networks_info:
            agent_ids = [
                agent["agent"]["agent_id"] for agent in network["network_agents"]
            ]
            agents = [id for id in add_agents if id not in agent_ids]
            if agents:
                payload = [
                    {
                        "agent_id": agent,
                    }
                    for agent in agents
                ]
                platform.create_network_agents(
                    payload, network["network"]["network_id"]
                )
                click.secho(
                    f"Added {len(agents)} endpoints to network {network['network']['network_name']}.",
                    fg="green",
                )
    if add_agents or remove_endpoint:
        networks_info = [
            platform.get_network_info(net["network_id"])["data"] for net in networks
        ]
    fields = [
        ("Endpoint ID", ("agent", "agent_id")),
        ("Endpoint Name", ("agent", "agent_name")),
        ("Public IPv4", ("agent", "agent_public_ipv4")),
    ]
    for network in networks_info:
        click.secho(f"Network: {network['network']['network_name']}:", fg="green")
        print_table(network["network_agents"], fields, to_json=json)


@apis.command()
@click.argument("network")
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    default=False,
    help="Forces to delete all matching networks.",
)
@syntropy_platform
def delete_network(network, yes, platform):
    """Delete a network."""
    networks = platform.index_networks(filter=f"id|name:{network}")["data"]

    for net in networks:
        if not yes and not confirm_deletion(net["network_name"], net["network_id"]):
            continue

        platform.delete_networks(net["network_id"])
        click.secho(
            f"Deleted network: {net['network_name']} (id={net['network_id']}).",
            fg="green",
        )


def main():
    apis(prog_name="syntropyctl")


if __name__ == "__main__":
    main()
