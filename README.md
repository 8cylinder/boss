
# Provision a server

## Dev

``` bash
uv sync
uv run boss --help
```

## Dev testing

``` bash
sudo snap install multipass

# Install the default image, LTS
multipass launch -n primary --cloud-init cloud-init.yaml

# Mount the boss dir in the ubuntu user's dir
multipass mount -t native . primary

# run the bash shell
multipass shell

# delete all multipass vms
multipass delete [--all|primary] && multipass purge

# Install pipx so UV can be installed
sudo apt install pipx
pipx install uv
# logout and login again.
uv --version
```

<!--
## Todo
- bash prompt
- bash history with dates

- final info not showing up
- set user on append_to_file
- phpinfo write to correct dir
- remove default public html dir if craft installed
- downloads to home, not current location
- phpinfo; if virtualhost use its dir instead
- phpinfo; user: use root if normal else use www-data
-->
