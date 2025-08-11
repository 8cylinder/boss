#!/usr/bin/env bash

# Default action if none provided
ACTION=${1}
VMNAME=boss

cd $HOME/projects/boss || exit

error() {
    echo -e "\e[31mError: $1\e[0m"
    exit 1
}

# Function to display usage
usage() {
    echo
    echo "Manage the $VMNAME multipass VM"
    echo
    echo "Usage: $0 [new|snapshot|restore|-h|--help]"
    echo "  n[ew]        Delete the $VMNAME vm and create a new one."
    echo "                 uv build, delete, purge, launch"
    echo "  sn[apshot]   Take a snapshot of the existing $VMNAME VM"
    echo "                 stop, snapshot, start"
    echo "  r[estore]    Restore the snapshot of the $VMNAME VM"
    echo "                 stop, restore, start"
    echo "  s[hell]      Open a shell in the $VMNAME VM"
    echo "  i[nfo]       Show information about the $VMNAME VM"
    echo "  -h, --help   Display this help message"
    exit 1
}

# Check for help flags first
if [ "$ACTION" = "-h" ] || [ "$ACTION" = "--help" ]; then
    usage
fi

# Convert to lowercase for case-insensitive matching
ACTION=$(echo "$ACTION" | tr '[:upper:]' '[:lower:]')

#set -x

case $ACTION in
    n*) # new
        uv build

        multipass delete $VMNAME
        multipass purge
        multipass launch -n $VMNAME --disk 20G --cloud-init cloud-init.yaml --mount . --mount dist
        ;;

    sn*) # snapshot
        if ! multipass info $VMNAME >/dev/null 2>&1; then
            error "The $VMNAME VM does not exist."
        fi
        multipass stop $VMNAME
        # multipass delete "${VMNAME}.snapshot1" >/dev/null 2>&1 || true
        multipass snapshot $VMNAME
        multipass start $VMNAME
        ;;

    s*) # shell
        if ! multipass info $VMNAME >/dev/null 2>&1; then
            error "The $VMNAME VM does not exist."
        fi
        multipass shell $VMNAME
        ;;

    r*) # restore
        if ! multipass info "${VMNAME}.snapshot1" >/dev/null 2>&1; then
            error "No snapshot for $VMNAME found. (use the 'snapshot' command first)"
        fi
        multipass stop $VMNAME
        multipass restore --destructive "${VMNAME}.snapshot1"
        multipass start $VMNAME
        ;;

    i*) # info
        multipass info $VMNAME
        ;;

    *)
        error "Invalid action: \"$ACTION\""
        ;;
esac
