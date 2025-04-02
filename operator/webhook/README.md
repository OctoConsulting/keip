# Metacontroller IntegrationRoute Lambda Controller

A python web server that implements
a [lambda controller from the Metacontroller API](https://metacontroller.github.io/metacontroller/concepts.html#lambda-controller).
The webhook will be called as part of the Metacontroller control loop when `IntegrationRoute` parent
resources are detected.  

The webhook contains two endpoints, `/sync` and `/addons/certmanager/sync`.
- `/sync`: The core logic that creates the Kubernetes resources for `IntegrationRoute`s.
- `/addons/certmanager/sync`: An add-on that creates a [cert-manager.io/v1.Certificate](https://cert-manager.io/docs/reference/api-docs/#cert-manager.io/v1.Certificate) based on annotations in an `IntegrationRoute`.


The format for the request and response JSON payloads can be
seen [here](https://metacontroller.github.io/metacontroller/api/compositecontroller.html#sync-hook)

### Dev Environment Setup

First, configure a Python virtual environment with version 3.11 or later (e.g.
using [venv](https://docs.python.org/3/library/venv.html)
or [conda](https://conda.io/projects/conda/en/latest/user-guide/getting-started.html#managing-python)).
Once that's set up, activate your virtual environment and run the following to install the necessary
packages:

```shell
pip install -r requirements-dev.txt
pip install -r requirements.txt
```

You should now be able to use the `Makefile` for running tests or starting a dev server, among other
tasks.

> **_NOTE:_**  There are some `make` tasks prefixed with `win-` in `Makefile` that are specific to Windows. 

#### Code Formatting

To keep diffs small, consider using
the [Black formatter](https://black.readthedocs.io/en/stable/integrations/editors.html).