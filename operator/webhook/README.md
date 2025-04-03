# Keip Integration Route Webhook

A Python web server that implements
a [lambda controller from the Metacontroller API](https://metacontroller.github.io/metacontroller/concepts.html#lambda-controller).
The webhook will be called as part of the Metacontroller control loop when `IntegrationRoute` parent
resources are detected.

The webhook contains two endpoints, `/sync` and `/addons/certmanager/sync`.

- `/sync`: The core logic that creates a `Deployment` from `IntegrationRoute` resources.
- `/addons/certmanager/sync`: An add-on that creates
  a [cert-manager.io/v1.Certificate](https://cert-manager.io/docs/reference/api-docs/#cert-manager.io/v1.Certificate)
  based on annotations in an `IntegrationRoute`.

The format for the request and response JSON payloads can be
seen [here](https://metacontroller.github.io/metacontroller/api/compositecontroller.html#sync-hook)

## Developer Guide

Requirements:

- Python v3.11

### Create the Python virtual environment

```shell
make venv
```

You should now have a [virtual environment](https://docs.python.org/3.11/library/venv.html) installed in `./venv` that
includes all the dependencies required by the project.
You can point your IDE of choice to `./venv/bin/python3` to enable its Python toolchain for this project.

### Run Tests

```shell
make test
```

### Run the Dev Server

```shell
make start-dev-server
```

### Code Formatting and Linting

To keep diffs small, we use the [Black](https://black.readthedocs.io/en/stable/index.html) formatter (included as part
of the `venv` install). [See here](https://black.readthedocs.io/en/stable/integrations/editors.html) for instructions on
integrating it with your editor.

```shell
make format
make lint
```

### Precommit Task

For convenience, there is a `precommit` task that runs unit tests, formatting, and linting. This task should be run
prior to every commit, as such you are encouraged to add it as
a [pre-commit git hook](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks).

```shell
make precommit
```

### Windows Development

There are Windows-compatible equivalents for most of the `make` commands listed above, prefixed with `win-` (
e.g. `test` -> `win-test`). See the [Makefile](Makefile) for more details.