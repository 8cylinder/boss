import enum
import sys
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import NamedTuple, ParamSpec, TypeVar

import click

from boss import out

# Type variable for the return type of the decorated function
R = TypeVar("R")
# Parameter specification for capturing all possible argument types
P = ParamSpec("P")


@dataclass
class Settings:
    """Represents application settings configuration.

    This class is used to manage and provide settings for the application.
    """

    timezone: str = "America/Los_Angeles"


class Args(NamedTuple):
    """A class representing configuration arguments for a specific operation.

    This class is used to store and manage various configurations and
    parameters required for a given task such as script generation,
    database operations, and module handling. It provides a structured
    way to group arguments and ensure proper data types.
    """

    bash: bool
    servername: str
    modules: tuple[str, ...]
    dry_run: bool
    required: bool
    dependencies: bool
    generate_script: bool
    dist_version: float | None
    new_user_and_pass: tuple[str, str]  # ...?
    sql_file: str | None
    db_name: str | None
    db_root_pass: str
    new_db_user_and_pass: tuple[str, str]
    new_system_user_and_pass: tuple[str, str]
    site_name_and_root: list[tuple[str, str, str]]
    craft_credentials: tuple[str, str, str]
    host_ip: str | None
    netdata_user_pass: tuple[str, str]
    wanted: list[str] = []


class Snap(enum.Enum):
    """An enumeration to represent different types of Snap."""

    CLASSIC = enum.auto()
    DEFAULT = enum.auto()


def warn(warning_message: str) -> Callable[[Callable[P, R]], Callable[P, R | None]]:
    """Require user confirmation before executing the decorated function."""

    def decorator(func: Callable[P, R]) -> Callable[P, R | None]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | None:
            # Ask user for confirmation
            out.print_fd(click.style(warning_message, fg="cyan"))
            out.print_fd(click.style("Continue? [y/N] ", fg="cyan"), nl=False)
            char = click.getchar(echo=True)
            if char == "y":
                return func(*args, **kwargs)
            click.secho("\nBoss halted.", fg="red")
            sys.exit(1)

        return wrapper

    return decorator
