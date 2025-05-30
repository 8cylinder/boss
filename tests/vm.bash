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
    echo "  s[napshot]   Take a snapshot of the existing $VMNAME VM"
    echo "  r[estore]    Restore the snapshot of the $VMNAME VM"
    echo "  -h, --help   Display this help message"
    exit 1
}

# Check for help flags first
if [ "$ACTION" = "-h" ] || [ "$ACTION" = "--help" ]; then
    usage
fi

# Convert to lowercase for case-insensitive matching
ACTION=$(echo "$ACTION" | tr '[:upper:]' '[:lower:]')

set -x

case $ACTION in
    n*)
        uv build

        multipass delete $VMNAME
        multipass purge
        multipass launch -n $VMNAME --cloud-init cloud-init.yaml --mount . --mount dist --mount tests
        multipass shell $VMNAME
        ;;

    s*)
        if ! multipass info $VMNAME >/dev/null 2>&1; then
            error "The $VMNAME VM does not exist."
        fi
        multipass stop $VMNAME
        multipass snapshot $VMNAME
        multipass start $VMNAME
        ;;

    r*)
        if ! multipass info "${VMNAME}.snapshot1" >/dev/null 2>&1; then
            error "No snapshot for $VMNAME found. (use the 'snapshot' command first)"
        fi
        multipass stop $VMNAME
        multipass restore --destructive "${VMNAME}.snapshot1"
        multipass start $VMNAME
        ;;

    *)
        error "Invalid action: \"$ACTION\""
        ;;
esac
