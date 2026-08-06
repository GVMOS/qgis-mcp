"""Every config shape install.py writes must carry SERVER_ENV.

Five builders spell the env block differently (env / environment / `set` lines /
--env flags), so a new client is easy to wire up without it.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def install():
    spec = importlib.util.spec_from_file_location("install_py", REPO_DIR / "install.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["install_py"] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("remote", [True, False])
def test_generic_entry_carries_server_env(install, remote):
    assert install._server_entry("cursor", remote)["env"] == install.SERVER_ENV


@pytest.mark.parametrize("remote", [True, False])
def test_opencode_entry_carries_server_env(install, remote):
    # opencode's key is "environment", not "env"
    assert install._opencode_server_entry(remote)["environment"] == install.SERVER_ENV


def test_hermes_bat_sets_server_env(install):
    bat = install._hermes_bat_content(remote=True)
    for key, value in install.SERVER_ENV.items():
        assert f"set {key}={value}\r\n" in bat


def test_auto_confirm_is_what_server_reads(install):
    """SERVER_ENV's value must be one the server accepts as truthy."""
    assert install.SERVER_ENV["QGIS_MCP_AUTO_CONFIRM"] in {"1", "true", "yes", "on"}
