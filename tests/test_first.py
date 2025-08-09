"""Tests for the First module in boss.mods.first using pytest."""

import pytest

from boss.dist import UbuntuVersion
from boss.engine import Args
from boss.mods.first import First


@pytest.fixture
def dummy_args() -> Args:
    """Return a dummy Args object for testing First module."""
    return Args(
        bash=True,
        servername="testserver",
        modules=(),
        dry_run=True,
        required=False,
        dependencies=False,
        generate_script=False,
        dist_version=None,
        new_user_and_pass=("user", "pass"),
        sql_file=None,
        db_name=None,
        db_root_pass="rootpass",  # noqa: S106
        new_db_user_and_pass=("dbuser", "dbpass"),
        new_system_user_and_pass=("sysuser", "syspass"),
        site_name_and_root=[],
        craft_credentials=("user", "email", "pass"),
        host_ip=None,
        netdata_user_pass=("user", "pass"),
        wanted=[],
    )


def test_first_ubuntu_14(dummy_args: Args) -> None:
    """Test that First selects correct packages for Ubuntu 14.04."""
    first = First(args=dummy_args, ubuntu_version=UbuntuVersion.V14_04, dry_run=True)
    assert "tree" in first.apt_pkgs
    assert "elinks" in first.apt_pkgs


def test_first_ubuntu_18(dummy_args: Args) -> None:
    """Test that First initializes apt_pkgs as a list for Ubuntu 18.04."""
    first = First(args=dummy_args, ubuntu_version=UbuntuVersion.V18_04, dry_run=True)
    assert isinstance(first.apt_pkgs, list)


def test_first_title(dummy_args: Args) -> None:
    """Test that the title attribute is set correctly."""
    first = First(args=dummy_args, ubuntu_version=UbuntuVersion.V20_04, dry_run=True)
    assert first.title == "First"


def test_first_ubuntu_24(dummy_args: Args) -> None:
    """Test that First selects correct packages for Ubuntu 24.04."""
    first = First(args=dummy_args, ubuntu_version=UbuntuVersion.V24_04, dry_run=True)
    assert "tree" in first.apt_pkgs
    assert "virt-what" in first.apt_pkgs
    assert "ripgrep" in first.apt_pkgs
    assert "fail2ban" in first.apt_pkgs
    assert "ssh" in first.apt_pkgs
    assert "trash-cli" in first.apt_pkgs


def test_first_pre_install_runs(dummy_args: Args, mocker: object) -> None:
    """Test that pre_install runs update and upgrade commands."""
    first = First(args=dummy_args, ubuntu_version=UbuntuVersion.V18_04, dry_run=True)
    mock_run = mocker.patch.object(first.mod, "run")
    first.pre_install()
    mock_run.assert_any_call("sudo apt-get update")
    mock_run.assert_any_call("sudo apt-get upgrade -y")


def test_first_post_install_emacs(
    dummy_args: Args,
    mocker: object,
) -> None:
    """Test that post_install sets timezone and installs emacs-nox."""
    first = First(args=dummy_args, ubuntu_version=UbuntuVersion.V18_04, dry_run=True)
    mock_run = mocker.patch.object(first.mod, "run")
    mock_is_apt_installed = mocker.patch.object(
        first,
        "is_apt_installed",
        return_value=False,
    )
    first.post_install()
    mock_run.assert_any_call("sudo apt install -y --no-install-recommends emacs-nox")
    mock_is_apt_installed.assert_called_with("fail2ban")


def test_first_post_install_restart_fail2ban(
    dummy_args: Args,
    mocker: object,
) -> None:
    """Test that post_install restarts fail2ban if installed."""
    first = First(args=dummy_args, ubuntu_version=UbuntuVersion.V18_04, dry_run=True)
    mock_run = mocker.patch.object(first.mod, "run")
    mocker.patch.object(first, "is_apt_installed", return_value=True)
    first.post_install()
    mock_run.assert_any_call("sudo systemctl restart fail2ban.service")


# def test_first_set_timezone_calls_run(
#     dummy_args: Args,
#     mocker: object,
# ) -> None:
#     """Test that set_timezone calls mod.run with the correct timezone."""
#     first = First(args=dummy_args, ubuntu_version=UbuntuVersion.V18_04, dry_run=True)
#     mock_run = mocker.patch.object(first.mod, "run")
#     first.set_timezone()
#     mock_run.assert_called_with("sudo timedatectl set-timezone testzone")


def test_first_install_web_server_calls_run(
    dummy_args: Args,
    mocker: object,
) -> None:
    """Test that install_web_server calls mod.run with tasksel command."""
    first = First(args=dummy_args, ubuntu_version=UbuntuVersion.V18_04, dry_run=True)
    mock_run = mocker.patch.object(first.mod, "run")
    first.install_web_server()
    mock_run.assert_called_with("sudo tasksel install web-server")
