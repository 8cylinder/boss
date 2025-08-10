# 👔 Boss, server provisioning tool


Boss is a Python-based tool for automated server provisioning and
configuration. It helps you set up servers with common stacks (LAMP, Craft
CMS, etc.), manage users, install packages, and apply best practices for
security and maintainability.

Boss is designed for both developers and
sysadmins who want to quickly bootstrap and manage Linux servers.

## Install

### Install uv

This project uses [uv](https://github.com/astral-sh/uv) for building and
managing dependencies.

To install uv if you don't have it yet, you can use one of the following methods:
``` bash
pip install uv
brew install uv
snap install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Download from GitHub

Clone the repository:

``` bash
git clone https://github.com/8cylinder/boss.git
```

### Install boss

``` bash
cd boss
uv sync
uv build
uv tool install dist/boss-[LATEST-BUILT-VERSION].whl
```

### Run boss

``` bash
boss --help
boss info --help
boss install --help
# boss has a man page also (thats cool!)
man boss
```

### Dev Usage

You can run boss directly in your dev environment using uv:

``` bash
uv run boss -h

# Or, to install it in editable mode for development:
uv tool install --editable .
```

## Server Install

To install boss on a remote server, the recommended way is to build a wheel
file and then install it using `pipx`.

1. Ensure you have `pipx` installed on your server:

    ``` bash
    sudo apt install pipx
    ```

1. Build the wheel file:

    ``` bash
    uv build
    ```

1. Copy the wheel file to your server (e.g., using scp):

    ``` bash
    scp dist/boss-*.whl user@server
    ```

1. SSH into your server and install with pipx:

    ``` bash
    pipx install /tmp/boss-*.whl
    pipx ensurepath
    # if you don't want to log out and back in, run:
    source ~/.bashrc
    ```
1. Now you can run boss on your server:

    ``` bash
    boss --help
    ```

## Usage

Here are some example commands to provision a server. Note the full module
name is not required, only enough chars to uniquely identify the module.

```bash
# See a list of available modules and any setting in the .env.boss if
# it exists.  Command line arguments will override the .env.boss settings.
boss info

# Get detailed information about the modules.
man boss

# Generate a .env.boss file with all mods and options.
boss info --write-env

# Install apache.
boss install apache

# Install apache and setup a virtual host.
boss install -d apache2 virtualhost \
--site-name-and-root=example.com,example,y \
--servername=example.com

# Install everything.
boss install AptProxy NewUserAsRoot Personalize LetsEncryptCert SelfCert \
Apache2 Nginx PhpBin Mysql Composer Xdebug PhpMyAdmin Adminer VirtualHost \
PhpInfo Craft Netdata Webmin Bashrc Firewall \
--host-ip=1.1.1.1 \
--new-system-user-and-pass=newuser,newpass \
--servername=example.com \
--db-name=example_db \
--db-root-pass=rootpass \
--site-name-and-root=example.com,example,y \
--craft-credentials=craftuser,craftuser@example.com,password \
--new-db-user-and-pass=dbuser,dbpass \
--dry-run  # Always use --dry-run first to see what will be installed.

# Output a bash script that can be written to a file and run later.
boss install apache --generate-script > install-apache.bash

# Output an ansible playbook that can be run later.
boss install apache --ansible > install-apache.yaml
```

## Tests

To run the test suite (requires pytest).  Note, these are *far* from complete.

```bash
uv run pytest
```
