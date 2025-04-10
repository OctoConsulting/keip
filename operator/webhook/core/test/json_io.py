import copy
import json
import os
from typing import Mapping

import pytest


@pytest.fixture()
def full_route(full_route_load: dict):
    return copy.deepcopy(full_route_load)


@pytest.fixture(scope="module")
def full_route_load() -> Mapping:
    cwd = os.path.dirname(os.path.abspath(__file__))
    return load_json_as_dict(f"{cwd}/json/full-iroute-request.json")


def load_json_as_dict(filepath: str) -> Mapping:
    with open(filepath, "r") as f:
        return json.load(f)
