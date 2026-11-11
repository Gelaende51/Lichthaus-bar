# Lichthaus-bar

[English](../../README.md) · **Deutsch**

Ein Statusleisten-Modul für [Lichthaus](https://github.com/Gelaende51/Lichthaus):
Waybar, i3blocks (i3bar, swaybar) und Polybar. Ein Python-3-Skript, nur die
Standardbibliothek. Unter KDE Plasma
[Lichthaus-plasma](https://github.com/Gelaende51/Lichthaus-plasma)
verwenden; für andere Systemabschnitte
[Lichthaus-tray](https://github.com/Gelaende51/Lichthaus-tray).

- **KI-Offenlegung**
  - Agent: Claude Code mit Claude Opus 5.5 (Anthropic) schrieb Code, Tests
    und Doku; etwa 1 M Token verarbeitet (größtenteils zwischengespeicherter
    Kontext), etwa 25 k erzeugt (Stand 2026-10-26).
  - Autor: wählte Entwurf, Formate und Klicks.

[Lizenz: AGPL-3.0](../../LICENSE) · [Notizen und Erkenntnisse](../../dev/takeaways.md)

## Was es tut

Es folgt dem ersten Widget des Lichthaus-Dienstes (Lampen und Auswahl der
ersten Instanz des Plasma-Widgets) über dessen ctl-Socket und gibt bei jeder
Änderung eine Zeile aus.

- **Text:** `--text "{icon} {brightness}%"` (Standard). Felder: `{icon}`
  `{brightness}` `{state}` `{name}` (die Auswahl) `{mode}` `{profile}`.
- **Symbole:** `--icons unicode` (Standard: ◉ an, ○ aus, ◌ nicht verbunden,
  ⊘ Dienst nicht erreichbar) oder `--icons nerd` (Nerd-Font-Glühbirnen).
- **Tooltip** (Waybar): jede Lampe mit an/aus, Helligkeit und Verbindung.
  Deutsch oder Englisch (nach Locale).
- **Zustände / CSS-Klassen:** `on`, `off`, `disconnected`, `unreachable`
  (der Dienst läuft nicht; es versucht es mit wachsendem Abstand erneut).
- **Klicks** rufen `lichthaus-bar toggle` (an/aus), `mode` (Automatisch /
  Manuell), `settings` (`lichthaus config`), `up` / `down` (Helligkeit ±5,
  wie das Mausrad des Plasma-Widgets).

## Installation

Braucht Lichthaus (Dienst läuft) und Python 3.

```sh
git clone <dieses Repository> Lichthaus-bar && cd Lichthaus-bar
./install.sh      # kopiert lichthaus-bar nach ~/.local/bin
```

`./uninstall.sh` entfernt es. Fertige Konfigurationen für Waybar
(`config.jsonc`, `style.css`), i3blocks und Polybar stehen in der
[englischen README](../../README.md#waybar): links an/aus, Mitte
Automatisch/Manuell, rechts Einstellungen, Mausrad dimmt.
