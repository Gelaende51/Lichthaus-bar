# Lichthaus-bar

**English** · [Deutsch](docs/i18n/README.de.md)

A status-bar module for [Lichthaus](https://github.com/Gelaende51/Lichthaus):
Waybar, i3blocks (i3bar, swaybar) and Polybar. One Python 3 script, standard
library only. On KDE Plasma use
[Lichthaus-plasma](https://github.com/Gelaende51/Lichthaus-plasma); for
other system trays, [Lichthaus-tray](https://github.com/Gelaende51/Lichthaus-tray).

- **AI disclosure**
  - Agent: Claude Code with Claude Opus 5.5 (Anthropic) wrote the code,
    tests and docs; about 1 M tokens processed (mostly cached context),
    about 25 k generated (as of 2026-10-26).
  - Author: chose the design, the formats and the clicks.

[License: AGPL-3.0](LICENSE) · [Notes and findings](dev/takeaways.md)

## What it does

It follows the Lichthaus service's first widget (the bulbs and selection
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
- **Clicks** run `lichthaus-bar toggle` (on/off), `mode` (Automatic /
  Manual), `settings` (`lichthaus config`), `up` / `down` (brightness ±5,
  as the Plasma widget's wheel).

## Install

Needs Lichthaus (its service running) and Python 3.

```sh
git clone <this repository> Lichthaus-bar && cd Lichthaus-bar
./install.sh      # copies lichthaus-bar to ~/.local/bin
```

`./uninstall.sh` removes it.

### Waybar

`config.jsonc`, then add `"custom/lichthaus"` to a modules list:

```jsonc
"custom/lichthaus": {
    "exec": "lichthaus-bar",            // --icons nerd, --text "{icon} {name}"
    "return-type": "json",
    "on-click": "lichthaus-bar toggle",
    "on-click-middle": "lichthaus-bar mode",
    "on-click-right": "lichthaus-bar settings",
    "on-scroll-up": "lichthaus-bar up",
    "on-scroll-down": "lichthaus-bar down"
}
```

`style.css`:

```css
#custom-lichthaus.on           { color: #f5c542; }
#custom-lichthaus.off          { opacity: 0.6; }
#custom-lichthaus.disconnected { color: #e0a030; }
#custom-lichthaus.unreachable  { color: #e05050; }
```

### i3blocks (i3bar, swaybar)

The block stays running; i3blocks writes clicks to its input, and the
script maps them (left, middle, right, wheel).

```ini
[lichthaus]
command=lichthaus-bar --format i3blocks
interval=persist
format=json
```

### Polybar

```ini
[module/lichthaus]
type = custom/script
exec = lichthaus-bar --format polybar
tail = true
click-left = lichthaus-bar toggle
click-middle = lichthaus-bar mode
click-right = lichthaus-bar settings
scroll-up = lichthaus-bar up
scroll-down = lichthaus-bar down
```

`--format text` prints plain lines for anything else.

## Development

```sh
python -m pytest tests   # fake socket; tests/test_mockdaemon.py runs an isolated mock daemon
```
