import os
import subprocess

from conftest import ROOT, SCRIPT


def test_install_and_uninstall_in_temp_home(tmp_path):
    env = dict(os.environ, HOME=str(tmp_path), PATH="/usr/bin:/bin")
    r = subprocess.run(["sh", str(ROOT / "install.sh")], env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    dest = tmp_path / ".local" / "bin" / "lichthaus-bar"
    assert dest.read_bytes() == SCRIPT.read_bytes()
    assert os.access(dest, os.X_OK)
    assert "not on PATH" in r.stdout
    v = subprocess.run([str(dest), "--version"], env=env, capture_output=True, text=True)
    assert v.returncode == 0 and v.stdout.strip()
    r = subprocess.run(["sh", str(ROOT / "uninstall.sh")], env=env, capture_output=True, text=True)
    assert r.returncode == 0 and not dest.exists()
    assert sorted(p.name for p in tmp_path.rglob("*") if p.is_file()) == []
