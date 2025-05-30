#!/usr/bin/env bash

cd $HOME/projects/boss || exit

uv build

multipass delete primary &&
multipass purge &&
multipass launch -n primary --cloud-init cloud-init.yaml --mount dist

multipass shell
