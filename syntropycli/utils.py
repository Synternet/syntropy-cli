import json

import click
import syntropy_sdk as sdk
from prettytable import PrettyTable
from syntropy_sdk.utils import *


def print_table(items, fields, to_json=False):
    """Prints either a pretty table using fields or a json from items.

    fields is a list of tuples, where the first element of the tuple represents the title of the field
    and the second element may be either an item's field name or a callable.
    Third element is optional and is used to format the field value.
    Also, if the second element is a list/tuple, then the fields will be retrieved recursively.

    NOTE: In such a case formatter function must accept all intermediate objects.

    Args:
        items (list[dict]): A list of items to generate the table for.
        fields (list[tuple]): Field definition.
        to_json (boolean): Outputs a JSON instead of a table if True.
    """

    def get_field(item, field):
        if item is None:
            return "-"
        field_param = field[0]
        field_formatter = (
            field[1] if len(field) == 2 else lambda x: x is None and "-" or x
        )
        if isinstance(field_param, (list, tuple)):
            field_value = item
            for subfield in field_param:
                field_value = get_field(field_value, [subfield])
                if not isinstance(field_value, dict):
                    break
        else:
            field_value = (
                field_param(item)
                if hasattr(field_param, "__call__")
                else item.get(field_param)
            )
        return field_formatter(field_value)

    if not to_json:
        table = PrettyTable()
        table.field_names = [field[0] for field in fields]
        for item in items:
            table.add_row([get_field(item, field[1:]) for field in fields])
        click.echo(str(table))
    else:
        click.echo(json.dumps(items, indent=4))


def find_by_name(items, name, field):
    """Finds an ID of an object with a corresponding name.

    NOTE: This is utterly inefficient for lists of names as it calls itself for each name.
    A faster implementation should be found to support larget `items` sizes.

    Args:
        items (iterable): A collection of objects to search for.
        name (Union[str, List[str]]): Either a single name or a list of names to look up.
        field (str): Field name prefix. "_name" and "_id" will be appended to get e.g. "api_key_id".

    Returns:
        Union[int, list[Union[int, None]], None]: found Ids for the provided names. Or None if not found.
    """
    if isinstance(name, (list, tuple)):
        return [find_by_name(items, nm, field) for nm in name]
    matching_ids = [
        item.get(f"{field}_id") for item in items if name == item.get(f"{field}_name")
    ]
    if len(matching_ids) != 1:
        click.secho(f'Could not find an id by name="{name}"', err=True, fg="red")
        return
    return matching_ids[0]


def collect_endpoint_services(services):
    def format_service_name(service):
        name = service["agent_service_name"]
        is_active = "^" if service["agent_service_is_active"] else "!"
        all_subnets = all(
            subnet["agent_service_subnet_is_active"]
            and subnet["agent_service_subnet_is_user_enabled"]
            for subnet in service["agent_service_subnets"]
        )
        any_subnets = any(
            subnet["agent_service_subnet_is_active"]
            and subnet["agent_service_subnet_is_user_enabled"]
            for subnet in service["agent_service_subnets"]
        )
        state_map = {
            (False, False): "!",
            (False, True): "~",
            (True, True): "^",
        }
        subnets_active = state_map[(all_subnets, any_subnets)]
        return f"{name}{is_active}{subnets_active}"

    services = ", ".join({format_service_name(service) for service in services})
    return services if services else "-"


def collect_connection_services(services):
    service_map = {}
    state_map = {
        sdk.AgentConnectionStatus.PENDING: "~",
        sdk.AgentConnectionStatus.WARNING: "*",
        sdk.AgentConnectionStatus.ERROR: "!",
        sdk.AgentConnectionStatus.CONNECTED: "^",
        sdk.AgentConnectionStatus.OFFLINE: "#",
    }
    for service in (
        services["agent_1"]["agent_services"] + services["agent_2"]["agent_services"]
    ):
        for subnet in service["agent_service_subnets"]:
            service_map[subnet["agent_service_subnet_id"]] = service[
                "agent_service_name"
            ]
    services = {
        f"{service_map[subnet['agent_service_subnet_id']]}{state_map.get(subnet['agent_connection_subnet_status'], '?')}"
        for subnet in services["agent_connection_subnets"]
        if subnet["agent_connection_subnet_is_enabled"]
    }
    return ", ".join(services) if services else "-"


def _validate_items(items):
    for item in items:
        if 0 <= len(item.strip()) < 3:
            click.secho(
                "Error: items must be longer than 3 characters.", err=True, fg="red"
            )
            raise SystemExit(1)


def _update_list(data, set_items, add_items, remove_items, clear_items, validate=True):
    data = list(data[:])
    if set_items:
        validate and _validate_items(set_items)
        data = list(item.strip() for item in set_items)
    if add_items:
        validate and _validate_items(add_items)
        data += [item.strip() for item in add_items if item not in data]
    if remove_items:
        data = [item.strip() for item in data if item not in remove_items]
    if clear_items:
        data = []
    return data
