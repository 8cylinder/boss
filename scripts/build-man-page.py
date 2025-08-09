#!/usr/bin/env python3

"""Build the man page for the Boss CLI."""

import datetime
import re
import shutil
import subprocess
import sys
from pathlib import Path

import click

try:
    from boss.cli import MODS
except ImportError:
    click.secho("This script must be run using UV.", fg="red")
    click.secho("> uv run scripts/build-man-page.py", fg="cyan")
    sys.exit(1)


def error(message: str) -> None:
    """Print an error message and exit the script."""
    click.secho(message, fg="red")
    sys.exit(1)


def run(command: list[str]) -> str:
    """Run a shell command and return its output."""
    output = ""
    try:
        output = subprocess.check_output(command, text=True)
        output = output.strip()
    except subprocess.CalledProcessError as e:
        error(f"Command '{' '.join(command)}' failed with error: {e}")
    return output


def get_date_and_version() -> tuple[str, str]:
    """Get the current date and Boss version."""
    # Get pretty date
    pretty_date = datetime.datetime.now().strftime("%Y-%m-%d")
    # Get version
    version = run(["boss", "--version"])
    version = re.sub(r"boss, version ", "", version.strip())
    return pretty_date, version


def get_install_options() -> str:
    """Get the options section from the help2man output."""
    # Get options using help2man
    options = run(["help2man", "boss install", "--version-string=0.0.0"])
    # Extract the OPTIONS section
    options_match = re.search(r'\.SH OPTIONS(.+?)\.SH "SEE ALSO"', options, re.DOTALL)
    if options_match:
        options = options_match.group(1).strip()
    else:
        error("Could not extract OPTIONS section from help2man output")
    return options


def get_info_options() -> str:
    """Get the options section from the help2man output."""
    # Get options using help2man
    options = run(["help2man", "boss info", "--version-string=0.0.0"])
    # Extract the OPTIONS section
    options_match = re.search(r'\.SH OPTIONS(.+?)\.SH "SEE ALSO"', options, re.DOTALL)
    if options_match:
        options = options_match.group(1).strip()
    else:
        error("Could not extract OPTIONS section from help2man output")
    return options


def unindent(text: str) -> str:
    """Remove leading whitespace from each line in the text.

    Uses the first line's indentation level to determine how much to remove.
    """
    lines = text.splitlines()
    if not lines:
        return ""
    # find the indent level of the first line.
    indent_level = len(lines[0]) - len(lines[0].lstrip())
    indent = " " * indent_level
    lines = [f"{indent}{i.strip()}" for i in lines]
    return "\n".join(lines)


def get_mods(full: bool = False) -> str:
    """Get the list of modules with their descriptions and requirements."""
    basic_template = unindent(""".B
        {name}
        .br""")
    full_template = unindent(""".TP
        .B {name}
        {description}

        {requirements}""")
    mods = []
    for mod in MODS:
        name = mod.__name__
        description = mod.__doc__ if mod.__doc__ else ""
        description = unindent(description)
        requirements = ""
        if mod.requires:
            requirements = r"\fBRequirements: \fI" + ", ".join(mod.requires) + r"\fR"
        lines = description.splitlines()
        if full:
            # lines = [i.strip() for i in lines]
            # fix bullets, add a .br after each line that starts with a number or a dash
            formatted = []
            for line in lines:
                formatted.append(line)
                if re.match(r"^([1-9]+\.|- )", line):
                    formatted.append(".br")
            description = "\n".join(formatted)
            mods.append(
                full_template.format(
                    name=name,
                    # description=description.strip(),
                    description=description,
                    requirements=requirements,
                ),
            )
        else:
            mods.append(basic_template.format(name=name))

    return "\n".join(mods)


def main() -> None:
    """Generate a formatted man page from a specified template file.

    It performs checks to ensure the presence of required files and tools,
    processes input data, and writes a newly formatted man page to the
    destination directory.
    """
    template = Path("scripts/boss.1.template")
    destination = Path("man")

    # Check if destination directory exists
    if not destination.exists():
        error(f"Destination directory {destination} does not exist.")

    # Check if template file exists
    if not template.exists():
        error(f"Template file {template} does not exist.")

    if shutil.which("help2man") is None:
        error("help2man is not installed. Please install it and try again.")

    # Run UV sync command
    subprocess.run(["uv", "sync"], check=True)

    pretty_date, version = get_date_and_version()

    install_options = get_install_options()
    info_options = get_info_options()

    mods = get_mods()

    details = get_mods(full=True)

    # Read the template file
    try:
        with template.open() as f:
            template_content = f.read()
    except OSError as e:
        error(f"Failed to read template file: {e}")

    # Replace placeholders
    template_content = template_content.format(
        version=version,
        date=pretty_date,
        install_options=install_options,
        info_options=info_options,
        modules=mods,
        details=details,
    )

    # Write to destination
    # dest_path = os.path.join(destination, "boss.1")
    dest_path = Path(destination, "boss.1")
    try:
        # with open(dest_path, "w") as f:
        with dest_path.open(mode="w") as f:
            f.write(template_content)
        print(f"Successfully created {dest_path}")
    except OSError as e:
        error(f"Failed to write to destination file: {e}")


if __name__ == "__main__":
    main()
