![Tests](https://github.com/SyntropyNet/syntropy-cli/workflows/Tests/badge.svg)
![PyPi](https://github.com/SyntropyNet/syntropy-cli/workflows/PyPi/badge.svg)

# Syntropy CLI
Syntropy CLI allows you to manage Syntropy endpoints and connections using command line interface. 

More information can be found at https://docs.syntropystack.com/docs/syntropyctl

## Requirements.

Python 3.7+

## Installation & Usage
### pip install

The latest package can be installed from PyPi:

```sh
pip install syntropycli
```

## Command line usage

In order to be able to perform operations with platform API keys, connections or endpoints you can use `syntropyctl` utility.
First you must set proper environment variables:

```sh
$ export SYNTROPY_API_SERVER={Syntropy Stack API URL}
$ export SYNTROPY_API_TOKEN={API authorization token}
```

The API authorization token can be retrieved from the Syntropy Stack.

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
  delete-api-key            Delete API key either by name or by id.
  delete-connection         Delete a connection.
  get-api-keys              List all API keys.
  get-connections           Retrieves connections.
  get-endpoints             List all endpoints.
  get-providers             Retrieve a list of endpoint providers.
```
