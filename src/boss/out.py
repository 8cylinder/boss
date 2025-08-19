"""Functions for controling the output.

These four function are the main interface for outputting.

- display_cmd: Pretty-print shell commands with optional wrapping and comments.
- title: Display formatted section titles with optional timestamps.
- warn: Display warning messages.
- notify: Display notice messages.
- error: Display error messages and optionally exit.

They make use of the print_fd function to direct output to the appropriate
file descriptor (stdout, stderr, or /dev/tty).  The /dev/tty output is meant for
messages that should always be seen by the user, even if stdout/stderr are
redirected.
"""

import datetime
import enum
import os
import random
import string
import sys
import textwrap

import click


class FD(enum.Enum):
    """Enumeration for standard file descriptors."""

    STDOUT = enum.auto()
    STDERR = enum.auto()
    INFO = enum.auto()


def print_fd(msg: str, *, fd: FD = FD.STDOUT, nl: bool = True) -> None:
    """Print a message to standard output."""
    if fd == FD.STDOUT:
        click.echo(msg, nl=nl)
    elif fd == FD.STDERR:
        click.echo(msg, err=True, nl=nl)
    elif fd == FD.INFO:
        end = "\n" if nl else ""
        # Get the TTY name associated with stdin (file descriptor 0)
        tty_device = os.ttyname(0)
        try:
            with open(tty_device, "w") as tty_fd:
                tty_fd.write(msg + end)
        except OSError as e:
            error(f"Error opening or writing to TTY: {e}")


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
        print_fd(click.style(fancy, fg="yellow"), fd=FD.STDOUT)
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
