"""Utility functions for BOSS scripts and commands."""

import datetime
import enum
import os
import random
import string
import sys
import textwrap
from pathlib import Path

import click


class FD(enum.Enum):
    """Enumeration for standard file descriptors."""

    STDOUT = enum.auto()
    STDERR = enum.auto()
    INFO = enum.auto()


def print_fd(msg: str, fd: FD = FD.STDOUT) -> None:
    """Print a message to standard output."""
    if fd == FD.STDOUT:
        click.echo(msg)
    elif fd == FD.STDERR:
        click.echo(msg, err=True)
    elif fd == FD.INFO:
        tty_path = Path("/dev/tty")
        try:
            tty_fd = os.open(tty_path.as_posix(), os.O_WRONLY | os.O_NOCTTY)
            with os.fdopen(tty_fd, "w") as f:
                f.write(msg + "\n")
        except OSError as e:
            click.echo(f"Error accessing TTY: {e}")

        # with os.fdopen(3, "w") as f:
        #     f.write(msg + "\n")

        # tty = Path("/dev/tty")
        # try:
        #     with tty.open() as f:
        #         f.write(msg)
        # except OSError:
        #     error_msg = "Could not open /dev/tty for writing info message."
        #     click.echo(error_msg, err=True)
        #     sys.exit(1)


def display_cmd(
    cmd: str,
    indent_count: int = 0,
    wrap: bool = True,
    script: bool = False,
    comment: str = "",
) -> None:
    """Display a command in a pretty format."""
    indent = " " * indent_count
    leader = "+ "
    initial_indent = indent + leader
    subsequent_indent = indent + (" " * len(leader))
    try:
        console_width = os.get_terminal_size().columns
    except OSError:
        console_width = 80
    if script:
        leader = ""
        initial_indent = ""
        subsequent_indent = "  "
        console_width = 80
        wrap = False if "<<" in cmd else True  # noqa: SIM211
    if wrap:
        w = textwrap.TextWrapper(
            initial_indent=initial_indent,
            subsequent_indent=subsequent_indent,
            break_on_hyphens=False,
            break_long_words=False,
            width=(console_width - len(subsequent_indent)),
        )
        lines = w.wrap(f"{cmd}")
        # Add a space & backslash to the end of each line then remove it from
        # the end of the joined string.
        fancy = "\n".join([f"{i} \\" for i in lines])[:-2]
    else:
        cmd_lines = cmd.split("\n")
        first = [initial_indent + cmd_lines[0]]
        rest = list(cmd_lines[1:])
        fancy = "\n".join(first + rest)

    if script:
        if comment:
            # sys.stdout.write(comment + "\n")
            print_fd(comment + "\n")
        # sys.stdout.write(fancy + "\n")
        print_fd(fancy + "\n")
    else:
        if comment:
            print_fd(click.style(comment, fg="yellow"))
        print_fd(click.style(fancy, fg="yellow"), fd=FD.INFO)
    sys.stdout.flush()


def title(msg: str, script: bool = False, show_date: bool = True) -> None:
    """Display a title in a pretty format."""
    timestamp = ""
    if show_date:
        timestamp = f" [{datetime.datetime.now().isoformat()}]"
    try:
        console_width = os.get_terminal_size().columns
    except OSError:
        console_width = 80
    if script:
        console_width = 80
        msg = f"# {msg} ".ljust(console_width, "-")
    else:
        msg = f"{msg}{timestamp} ".ljust(console_width, "-")
    print_fd("", fd=FD.INFO)
    if not script:
        print_fd(click.style(msg, bold=True), fd=FD.INFO)
    else:
        print_fd(msg + "\n", fd=FD.STDOUT)
    sys.stdout.flush()


def warn(msg: str, script: bool = False) -> None:
    """Display a warning message in a pretty format."""
    if script:
        sys.stdout.write(f"# !!! WARNING: {msg} !!!\n")
    else:
        print_fd(
            click.style("WARNING: ", fg="yellow", bold=True)
            + click.style(str(msg), fg="yellow"),
            fd=FD.STDERR,
        )
    sys.stdout.flush()


def notify(msg: str) -> None:
    """Display a notice message in a pretty format."""
    print_fd(
        click.style("NOTICE: ", fg="blue", bold=True)
        + click.style(str(msg), fg="blue"),
        fd=FD.INFO,
    )
    sys.stdout.flush()


def error(msg: str, dry_run: bool = False) -> None:
    """Display an error message in a pretty format and exit."""
    print_fd(
        click.style("ERROR: ", fg="red", bold=True) + click.style(str(msg), fg="red"),
        fd=FD.STDERR,
    )
    sys.stdout.flush()
    if not dry_run:
        sys.exit(1)


def password_gen(level: str = "alpha-num", length: int = 10) -> str:
    """Generate a random password."""
    levels = {
        "alpha-lower": string.ascii_lowercase,
        "alpha-mixed": string.ascii_letters,
        "alpha-num": string.ascii_letters + string.digits,
        "alpha-num-symbol": string.ascii_letters + string.digits + string.punctuation,
    }
    source: str = ""
    try:
        source = levels[level]
    except KeyError:
        error("password level not one of: {}".format(", ".join(levels.keys())))
    return "".join(random.choices(source, k=length))  # noqa: S311
