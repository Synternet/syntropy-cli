![Tests](https://github.com/SyntropyNet/syntropy-cli/workflows/Tests/badge.svg)
![PyPi](https://github.com/SyntropyNet/syntropy-cli/workflows/PyPi/badge.svg)

# Syntropy CLI
Syntropy CLI allows you to manage Syntropy endpoints, networks, and connections using command line interface. 

## Requirements.

Python 3.6+

## Installation & Usage
### pip install

The latest package can be installed from PyPi:

```sh
pip install syntropycli
```

## Command line usage

In order to be able to perform operations with platform API keys, networks, connections or endpoints you can use `syntropyctl` utility.
First you must set proper environment variables:

```sh
$ export SYNTROPY_API_SERVER={Syntropy Stack API URL}
$ export SYNTROPY_API_TOKEN={API authorization token}
```

In case you have a registered user on the platform you can retrieve the API token using this command(deprecated):

```sh
$ syntropyctl login {user name} {password}
{your API authorization token}
```

You can omit `{password}` on the command line, then the utility will ask you to type the password.

In case you are using SSO to login to the platform the API authorization token can be retrieved from the Platform itself.

Or you can set the `SYNTROPY_API_TOKEN` environment variable like this(Set `SYNTROPY_API_SERVER` to the server address and `SYNTROPY_API_TOKEN` to empty value before that):

```sh
export SYNTROPY_API_TOKEN=`syntropyctl login {user name} {password}`
```

You can learn about the types of actions this utility can perform by running:

```sh
$ syntropyctl --help
Usage: syntropyctl [OPTIONS] COMMAND [ARGS]...

  Syntropy Networks cli tool

Options:
  --help  Show this message and exit.

Commands:
  configure-endpoints       Configures an endpoint with provided provider,...
  create-api-key            Create a API key.
  create-connections        Create connections between endpoints.
  create-network            Create a network.
  delete-api-key            Delete API key either by name or by id.
  delete-connection         Delete a connection.
  delete-network            Delete a network.
  get-api-keys              List all API keys.
  get-connections           Retrieves network connections.
  get-endpoints             List all endpoints.
  get-networks              List all networks.
  get-providers             Retrieve a list of providers.
  get-topology              Retrieves networks topology.
  login                     Login with username and password.
  manage-network-endpoints  Add/Remove endpoints to/from a network.
```
