# Haus.Licht-bar

**English** · [Deutsch](docs/i18n/README.de.md)

A status-bar module for [Haus.Licht](https://github.com/Gelaende51/Haus.Licht):
Waybar, i3blocks (i3bar, swaybar) and Polybar. One Python 3 script, standard
library only. On KDE Plasma use
[Haus.Licht-plasma](https://github.com/Gelaende51/Haus.Licht-plasma); for
other system trays, [Haus.Licht-tray](https://github.com/Gelaende51/Haus.Licht-tray).

- **AI disclosure**
  - Agent: Claude Code with Claude Opus 5.5 (Anthropic) wrote the code,
    tests and docs; about 1 M tokens processed (mostly cached context),
    about 25 k generated (as of 2026-10-26).
  - Author: chose the design, the formats and the clicks.

[License: AGPL-3.0](LICENSE) · [Notes and findings](dev/takeaways.md)

## What it does

It follows the Haus.Licht service's first widget (the bulbs and selection
of the Plasma widget's first instance) over its ctl socket and prints one
line per change.

- **Text:** `--text "{icon} {brightness}%"` (default). Fields: `{icon}`
  `{brightness}` `{state}` `{name}` (the selection) `{mode}` `{profile}`.
- **Icons:** `--icons unicode` (default: ◉ on, ○ off, ◌ not connected,
  ⊘ service unreachable) or `--icons nerd` (Nerd Font bulbs).
- **Tooltip** (Waybar): each bulb with on/off, brightness and link. English
  and German (the locale).
- **States / CSS classes:** `on`, `off`, `disconnected`, `unreachable`
  (the service is not running; it retries with back-off).
- **Clicks** run `hauslicht-bar toggle` (on/off), `mode` (Automatic /
  Manual), `settings` (`hauslicht config`), `up` / `down` (brightness ±5,
  as the Plasma widget's wheel).

## Install

Needs Haus.Licht (its service running) and Python 3.

```sh
git clone <this repository> Haus.Licht-bar && cd Haus.Licht-bar
./install.sh      # copies hauslicht-bar to ~/.local/bin
```

`./uninstall.sh` removes it.

### Waybar

`config.jsonc`, then add `"custom/hauslicht"` to a modules list:

```jsonc
"custom/hauslicht": {
    "exec": "hauslicht-bar",            // --icons nerd, --text "{icon} {name}"
    "return-type": "json",
    "on-click": "hauslicht-bar toggle",
    "on-click-middle": "hauslicht-bar mode",
    "on-click-right": "hauslicht-bar settings",
    "on-scroll-up": "hauslicht-bar up",
    "on-scroll-down": "hauslicht-bar down"
}
```

`style.css`:

```css
#custom-hauslicht.on           { color: #f5c542; }
#custom-hauslicht.off          { opacity: 0.6; }
#custom-hauslicht.disconnected { color: #e0a030; }
#custom-hauslicht.unreachable  { color: #e05050; }
```

### i3blocks (i3bar, swaybar)

The block stays running; i3blocks writes clicks to its input, and the
script maps them (left, middle, right, wheel).

```ini
[hauslicht]
command=hauslicht-bar --format i3blocks
interval=persist
format=json
```

### Polybar

```ini
[module/hauslicht]
type = custom/script
exec = hauslicht-bar --format polybar
tail = true
click-left = hauslicht-bar toggle
click-middle = hauslicht-bar mode
click-right = hauslicht-bar settings
scroll-up = hauslicht-bar up
scroll-down = hauslicht-bar down
```

`--format text` prints plain lines for anything else.

## Development

```sh
python -m pytest tests   # fake socket; tests/test_mockdaemon.py runs an isolated mock daemon
```
