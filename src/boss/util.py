# run-shell-command :: ../build.bash

import sys
import os
import datetime
import textwrap
import click
import string
import random


def display_cmd(
    cmd: str,
    indent_count: int = 0,
    wrap: bool = True,
    script: bool = False,
    comment: str = "",
) -> None:
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
        wrap = False if "<<" in cmd else True
    if wrap:
        w = textwrap.TextWrapper(
            initial_indent=initial_indent,
            subsequent_indent=subsequent_indent,
            break_on_hyphens=False,
            break_long_words=False,
            width=(console_width - len(subsequent_indent)),
        )
        lines = w.wrap("{}".format(cmd))
        # Add a space & backslash to the end of each line then remove it from
        # the end of the joined string.
        fancy = "\n".join(["{} \\".format(i) for i in lines])[:-2]
    else:
        cmd_lines = cmd.split("\n")
        first = [initial_indent + cmd_lines[0]]
        rest = [i for i in cmd_lines[1:]]
        fancy = "\n".join(first + rest)

    if not script:
        if comment:
            click.secho(comment, fg="yellow")
        click.secho(fancy, fg="yellow")
    else:
        if comment:
            sys.stdout.write(comment + "\n")
        sys.stdout.write(fancy + "\n")
    sys.stdout.flush()


def title(msg: str, script: bool = False, show_date: bool = True) -> None:
    timestamp = ""
    if show_date:
        timestamp = " [{}]".format(datetime.datetime.now().isoformat())
    try:
        console_width = os.get_terminal_size().columns
    except OSError:
        console_width = 80
    if script:
        console_width = 80
        msg = "# {} ".format(msg).ljust(console_width, "-")
    else:
        msg = "{}{} ".format(msg, timestamp).ljust(console_width, "-")
    print()
    if not script:
        click.secho(msg, bold=True)
    else:
        sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def warn(msg: str, script: bool = False) -> None:
    if script:
        sys.stdout.write("# !!! WARNING: {} !!!\n".format(msg))
    else:
        click.echo(
            click.style("WARNING: ", fg="yellow", bold=True)
            + click.style(str(msg), fg="yellow")
        )
    sys.stdout.flush()


def notify(msg: str) -> None:
    click.echo(
        click.style("NOTICE: ", fg="blue", bold=True) + click.style(str(msg), fg="blue")
    )
    sys.stdout.flush()


def error(msg: str, dry_run: bool = False) -> None:
    click.echo(
        click.style("ERROR: ", fg="red", bold=True) + click.style(str(msg), fg="red")
    )
    sys.stdout.flush()
    if not dry_run:
        sys.exit(1)


def password_gen(level: str = "alpha-num", length: int = 10) -> str:
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
    return "".join(random.choices(source, k=length))
