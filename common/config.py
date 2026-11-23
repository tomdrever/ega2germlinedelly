import json
from typing import TypeVar

from common.util import fail
from models import BaseConfig

ConfigT = TypeVar("ConfigT", bound=BaseConfig)


def load_config(path: str, cls: type[ConfigT]) -> ConfigT:
    """Load a JSON config file into `cls`, exiting with a readable message on any problem.

    Unknown or missing keys are errors, so a config written for one workflow
    can't silently be used by another.
    """
    try:
        with open(path) as fh:
            data = json.load(fh)
    except FileNotFoundError:
        fail(f"Config file {path} not found - copy {path}.template and fill it out")
    except json.JSONDecodeError as e:
        fail(f"Could not parse {path} as JSON: {e}")

    if not isinstance(data, dict):
        fail(f"{path} must contain a JSON object")

    try:
        return cls(**data)
    except TypeError as e:
        fail(f"Invalid config in {path}: {e}")
