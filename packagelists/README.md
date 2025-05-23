To generate a list of all packages available:
`apt-cache dump | grep 'Package:.*' | sed 's/Package: //' | sort > ubuntu-24.04-allpackages`

