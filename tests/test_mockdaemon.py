"""Against a real Lichthaus daemon with mock bulbs only, fully isolated:
its own state file, socket, config/cache/state directories, HOME, no session
bus and no Bluetooth (LICHTHAUS_BACKENDS=mock). Skipped without a checkout."""
import json
import os
import sys
import subprocess
import time
from pathlib import Path

import pytest

from conftest import SCRIPT, load_bar

client = load_bar()

HL = Path(os.environ.get("LICHTHAUS_CHECKOUT", Path.home() / "building_stuff" / "Lichthaus"))
PY = HL / ".venv" / "bin" / "python"
LIVE_FILES = [HL / "lichthaus.json", Path.home() / ".config" / "lichthaus" / "lichthaus.json"]

pytestmark = pytest.mark.skipif(not (HL / "lichthaus").exists() or not PY.exists(),
                                reason="no Lichthaus checkout")


def isolated_env(d: Path) -> dict:
    home = d / "home"
    home.mkdir(exist_ok=True)
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "XDG_CACHE_HOME": str(home / ".cache"),
        "XDG_STATE_HOME": str(home / ".local" / "state"),
        "XDG_DATA_HOME": str(home / ".local" / "share"),
        "XDG_RUNTIME_DIR": str(d),
        "DBUS_SESSION_BUS_ADDRESS": f"unix:path={d}/no-bus",
        "LICHTHAUS_STATE": str(d / "state.json"),
        "LICHTHAUS_SOCK": str(d / "d.sock"),
        "LICHTHAUS_BACKENDS": "mock",
        "LICHTHAUS_NO_PANEL": "1",
        "LANG": "C.UTF-8",
    }


def stamp(p: Path):
    try:
        s = p.stat()
        return (s.st_mtime_ns, s.st_size)
    except FileNotFoundError:
        return None


@pytest.fixture
def mock_daemon(short_dir):
    env = isolated_env(short_dir)
    # Confirm beforehand where it would read and write.
    out = subprocess.run([str(PY), "-c", "from haus import common; print(common.STATE_PATH);"
                          "print(common.SOCK_PATH); print(common.lock_path(common.STATE_PATH))"],
                         cwd=HL, env=env, capture_output=True, text=True, check=True).stdout.split("\n")
    assert out[0] == env["LICHTHAUS_STATE"]
    assert out[1] == env["LICHTHAUS_SOCK"]
    assert out[2].startswith(str(short_dir))
    for p in LIVE_FILES:
        assert str(p) not in out
    before = [stamp(p) for p in LIVE_FILES]
    log = open(short_dir / "daemon.log", "w")
    proc = subprocess.Popen([str(HL / "lichthaus"), "sync", "--no-desktop-writes"], cwd=short_dir,
                            env=env, stdout=log, stderr=subprocess.STDOUT)
    sock = Path(env["LICHTHAUS_SOCK"])
    try:
        end = time.time() + 30
        while time.time() < end:
            try:
                client.request(["get"], path=sock, timeout=2)
                break
            except client.Unreachable:
                time.sleep(0.2)
        else:
            pytest.fail("mock daemon did not start: " + (short_dir / "daemon.log").read_text()[-2000:])
        yield sock
    finally:
        proc.terminate()
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            proc.kill()
        log.close()
        assert [stamp(p) for p in LIVE_FILES] == before


def test_line_changes_with_state(mock_daemon, short_dir):
    sock = mock_daemon
    assert client.request(["add", "mock", "name=Desk"], path=sock)["added"] == "mock:1"
    env = isolated_env(short_dir)
    p = subprocess.Popen([sys.executable, str(SCRIPT), "--format", "waybar"], env=env,
                         stdout=subprocess.PIPE, text=True)
    try:
        first = json.loads(p.stdout.readline())
        assert first["class"] == "on" and "Desk: on" in first["tooltip"]
        assert subprocess.run([sys.executable, str(SCRIPT), "toggle"], env=env,
                              timeout=20).returncode == 0
        second = json.loads(p.stdout.readline())
        assert second["class"] == "off" and second != first
        print("before:", first["text"], "| after:", second["text"])
    finally:
        p.terminate()
        p.wait(10)
