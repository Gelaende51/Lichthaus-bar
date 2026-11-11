import json
import os
import queue
import subprocess
import sys
import threading
import time

import pytest

from conftest import SCRIPT, sample_state


def wait_for(cond, timeout=5.0):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.02)
    return False


@pytest.fixture
def english(monkeypatch):
    for v in ("LC_ALL", "LC_MESSAGES"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("LANG", "C.UTF-8")


# --- output formats ---------------------------------------------------------

def test_waybar_json(bar, english):
    line = bar.render(sample_state(), "waybar")
    obj = json.loads(line)
    assert set(obj) == {"text", "tooltip", "class", "percentage", "alt"}
    assert obj["class"] == "disconnected" or obj["class"] in ("on", "off")
    st = sample_state(link="connected")
    obj = json.loads(bar.render(st, "waybar"))
    assert obj["class"] == "on" and obj["alt"] == "on" and obj["percentage"] == 50
    assert obj["text"] == "◉ 50%"
    assert "\n" not in line


def test_classes(bar, english):
    assert bar.state_class(None) == "unreachable"
    assert bar.state_class(sample_state(link="connected", power=True)) == "on"
    assert bar.state_class(sample_state(link="connected", power=False)) == "off"
    assert bar.state_class(sample_state(link="held")) == "disconnected"
    assert bar.state_class(sample_state(link="failed")) == "disconnected"
    assert bar.state_class(sample_state(link="connected", connected=False)) == "disconnected"
    obj = json.loads(bar.render(None, "waybar"))
    assert obj["class"] == "unreachable" and obj["percentage"] == 0
    assert obj["tooltip"] == "Lichthaus service not reachable"


def test_waybar_escapes_markup(bar, english):
    st = sample_state(link="connected")
    st["bulbs_list"][0]["name"] = "Desk & <Lamp>"
    obj = json.loads(bar.render(st, "waybar"))
    assert "Desk &amp; &lt;Lamp&gt;" in obj["tooltip"]


def test_other_formats(bar, english):
    st = sample_state(link="connected", power=False)
    i3 = json.loads(bar.render(st, "i3blocks"))
    assert i3["full_text"] == "○ 50%" and i3["urgent"] is False
    assert json.loads(bar.render(None, "i3blocks"))["urgent"] is True
    assert bar.render(st, "polybar") == "○ 50%"
    assert bar.render(st, "text") == "○ 50%"
    assert bar.render(None, "text") == "⊘ –%"


def test_template(bar, english):
    st = sample_state(link="connected", selected="mock:1", following=False)
    t = "{icon} {name} {state} {brightness}% {mode} {profile} {nope}"
    assert bar.render(st, "text", t) == "◉ Desk on 50% Manual default {nope}"
    assert bar.render(sample_state(link="connected"), "text", "{name}") == "All bulbs"
    assert bar.render(st, "text", "{broken") == "{broken"


def test_icon_sets(bar, english):
    for name, icons in bar.ICONS.items():
        assert set(icons) == {"on", "off", "disconnected", "unreachable"}
        assert len(set(icons.values())) == 4
    assert bar.render(sample_state(link="connected"), "text", "{icon}", "nerd") == "\U000f0335"
    assert bar.render(None, "text", "{icon}", "nerd") == "\U000f0e4f"


def test_tooltip_english_and_german(bar, monkeypatch, english):
    tip = bar.view(sample_state())["tooltip"].split("\n")
    assert tip[0] == "Lichthaus · All bulbs · Automatic"
    assert "Desk: on, 50 %, connected" in tip
    assert "Shelf: off, 0 %, held" in tip
    assert not any("Unused" in t for t in tip)  # not in the widget
    monkeypatch.setenv("LANG", "de_DE.UTF-8")
    tip = bar.view(sample_state())["tooltip"].split("\n")
    assert tip[0] == "Lichthaus · Alle Lampen · Automatisch"
    assert "Desk: an, 50 %, verbunden" in tip
    assert "Shelf: aus, 0 %, getrennt (gehalten)" in tip
    assert bar.view(None)["tooltip"] == "Lichthaus-Dienst nicht erreichbar"
    monkeypatch.setenv("LC_ALL", "en_GB.UTF-8")
    assert bar.view(None)["tooltip"] == "Lichthaus service not reachable"


def test_old_protocol_hint(bar, english):
    st = sample_state(link="connected")
    st.pop("protocol")
    assert "too old" in bar.view(st)["tooltip"]


# --- subcommands -----------------------------------------------------------

def run_cli(args, env_extra, **kw):
    env = dict(os.environ, **env_extra)
    return subprocess.run([sys.executable, str(SCRIPT)] + args, env=env,
                          capture_output=True, text=True, timeout=20, **kw)


@pytest.mark.parametrize("sub,sent", [
    ("toggle", [["toggle"]]),
    ("up", [["nudge", "5"]]),
    ("down", [["nudge", "-5"]]),
])
def test_subcommands(fake, sub, sent):
    r = run_cli([sub], {"LICHTHAUS_SOCK": str(fake.path)})
    assert r.returncode == 0, r.stderr
    assert [[q["cmd"]] + q["args"] for q in fake.requests] == sent
    assert all(q["which"] is None for q in fake.requests)


def test_mode_subcommand(fake, bar):
    env = {"LICHTHAUS_SOCK": str(fake.path)}
    # Following, lit bulbs at different levels (Desk 50, Shelf off): pause.
    fake.state["bulbs_list"][1]["power"] = True
    fake.state["bulbs_list"][1]["output"] = 30.0
    assert run_cli(["mode"], env).returncode == 0
    assert [[q["cmd"]] + q["args"] for q in fake.requests] == [["get"], ["pause"]]
    # One lit bulb: hold its exact level with `dim` (as the widget).
    fake.requests.clear()
    fake.state["bulbs_list"][1]["power"] = False
    assert run_cli(["mode"], env).returncode == 0
    assert [[q["cmd"]] + q["args"] for q in fake.requests] == [["get"], ["dim", "50.0"]]
    # Manual: back to Automatic.
    fake.requests.clear()
    fake.state["following"] = False
    assert run_cli(["mode"], env).returncode == 0
    assert [[q["cmd"]] + q["args"] for q in fake.requests] == [["get"], ["resume"]]


def test_subcommand_unreachable(short_dir):
    r = run_cli(["toggle"], {"LICHTHAUS_SOCK": str(short_dir / "none.sock")})
    assert r.returncode == 1 and "lichthaus-bar:" in r.stderr


def test_settings_runs_lichthaus_config(short_dir, fake):
    bindir = short_dir / "bin"
    bindir.mkdir()
    log = short_dir / "called"
    fake_hl = bindir / "lichthaus"
    fake_hl.write_text(f'#!/bin/sh\necho "$@" > "{log}"\n')
    fake_hl.chmod(0o755)
    r = run_cli(["settings"], {"PATH": f"{bindir}:{os.environ['PATH']}",
                               "LICHTHAUS_SOCK": str(fake.path)})
    assert r.returncode == 0, r.stderr
    assert wait_for(lambda: log.exists() and log.read_text().strip() == "config")
    assert fake.requests == []  # no ctl command


def test_click_from_line(bar):
    assert bar.click_from_line('{"name":"lichthaus","button":1,"x":3}') == "toggle"
    assert bar.click_from_line("2") == "mode"
    assert bar.click_from_line('{"button":3}') == "settings"
    assert bar.click_from_line('{"button":4}') == "up"
    assert bar.click_from_line('{"button":5}') == "down"
    assert bar.click_from_line('{"button":9}') is None
    assert bar.click_from_line("junk") is None


# --- following the daemon --------------------------------------------------

class Lines:
    def __init__(self, proc):
        self.q = queue.Queue()
        self.all = []
        threading.Thread(target=self._read, args=(proc.stdout,), daemon=True).start()

    def _read(self, f):
        for line in f:
            self.q.put(line.rstrip("\n"))

    def next(self, timeout=5):
        line = self.q.get(timeout=timeout)
        self.all.append(line)
        return line


def follow_proc(sock, *extra):
    env = dict(os.environ, LICHTHAUS_SOCK=str(sock), LANG="C.UTF-8")
    env.pop("LC_ALL", None)
    return subprocess.Popen([sys.executable, str(SCRIPT), "--base-delay", "0.05",
                             "--max-delay", "0.4", *extra], env=env,
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)


def test_follow_reconnects_with_unreachable_state(fake):
    fake.state["link"] = "connected"
    p = follow_proc(fake.path)
    try:
        out = Lines(p)
        assert json.loads(out.next())["class"] == "on"
        fake.state["power"] = False
        fake.push({"event": "intended", "bulb": "mock:1", "power": False})
        assert json.loads(out.next())["class"] == "off"
        fake.stop()
        down = json.loads(out.next())
        assert down["class"] == "unreachable" and down["text"] == "⊘ –%"
        fake.state["power"] = True
        fake.start()
        assert json.loads(out.next(timeout=5))["class"] == "on"
        # Unchanged states print nothing.
        with pytest.raises(queue.Empty):
            out.next(timeout=0.6)
    finally:
        p.terminate()
        p.wait(5)


def test_i3blocks_clicks_from_stdin(fake):
    fake.state["link"] = "connected"
    p = follow_proc(fake.path, "--format", "i3blocks")
    try:
        out = Lines(p)
        assert json.loads(out.next())["full_text"] == "◉ 50%"
        p.stdin.write('{"name":"lichthaus","button":1}\n')
        p.stdin.flush()
        assert wait_for(lambda: any(q["cmd"] == "toggle" for q in fake.requests))
        p.stdin.write('{"button":5}\n')
        p.stdin.flush()
        assert wait_for(lambda: any(q["cmd"] == "nudge" and q["args"] == ["-5"]
                                    for q in fake.requests))
    finally:
        p.terminate()
        p.wait(5)
