
# Provision a server

## Dev

``` bash
uv sync
uv run boss --help
```

## Dev testing

Use multipass to run VMs for testing.

``` bash
sudo snap install multipass
./tests/vm.bash -h
./tests/vm.bash new
multipass shell
```

In the VM, run to install boss.

``` bash
# Install boss using the wheel file
pipx install dist/boss-*.whl
pipx ensurepath
source ~/.bashrc
```

### test commands

``` bash
boss install boss.local comp self pers apache phpbin mysql craft virt -N boss -A boss,password -s boss.local,boss,y -c sm,sheldon@8cylinder.com,password

boss install boss.local craft -N boss -A boss,password -s boss.local,boss,y -c sm,sheldon@8cylinder.com,password -o 
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
