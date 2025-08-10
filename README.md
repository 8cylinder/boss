# Boss: automated server provisioning

Boss is a Python-based tool for automated server provisioning and
configuration. It helps you set up servers with common stacks (LAMP, Craft
CMS, etc.), manage users, install packages, and apply best practices for
security and maintainability.

Boss is designed for both developers and
sysadmins who want to quickly bootstrap and manage Linux servers.

## Install

### Install uv

This project uses [uv](https://github.com/astral-sh/uv) for building and managing dependencies.

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
boss install apache phpbin mysql craft virt -N boss -A boss,password \
-s boss.local,boss,y -c sm,sheldon@8cylinder.com,password

boss info
```

## Tests

To run the test suite (requires pytest).  Note these are *far* from complete.

```bash
uv run pytest
```
