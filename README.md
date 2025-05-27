
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
multipass launch

# Mount the boss dir in the ubuntu user's dir
multipass mount -t native . primary

# run the bash shell
multipass shell

# Install pipx so UV can be installed
sudo install pipx
pipx install uv
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
