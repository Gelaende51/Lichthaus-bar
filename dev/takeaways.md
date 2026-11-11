# Takeaways

## One script, the client copied in

The bar must stay standard-library only and installable as one file, so
Lichthaus-tray's `client.py` (request, protocol check, `Watcher` with
back-off and debounced `get`) is copied into `lichthaus-bar` rather than
imported. A fix there needs copying here too. The tests load the script
(no `.py` name) through `importlib.machinery.SourceFileLoader`.

## The wheel is `nudge ±5`, not the device step

The brief asked for "the device step, as the widget's wheel does". The
Plasma widget's wheel sends `nudge 5` / `nudge -5` per notch
(`main.qml`, `onWheel`); the device `step` only sets the slider's
resolution. `up` / `down` send the same as the wheel.

## Automatic -> Manual is not just `pause`

As in the widget's `setManual()`: when the selection's lit bulbs share
one level, `dim <level>` holds it exactly (`pause` sends nothing and `get`
then reports no output until the next level); otherwise `pause`. Manual ->
Automatic is `resume`.

## i3blocks clicks reach a persistent block on stdin

A block with `interval=persist` keeps running, so i3blocks cannot run a
command per click; it writes the click to the block's stdin (a JSON object
with `button` when `format=json`). The script reads them in i3blocks mode
and maps 1/2/3/4/5 to toggle/mode/settings/up/down. Waybar and Polybar run
the subcommands themselves.

## Waybar reads text and tooltip as Pango markup

A bulb named `A & B` would break the markup; `&`, `<`, `>` are escaped in
the Waybar format only.

## Testing beside the live daemon

As in Lichthaus-tray: the mock-daemon test gives the daemon its own state
file, socket, HOME and XDG directories, no session bus and
`LICHTHAUS_BACKENDS=mock`, confirms the paths first and checks the live
files' mtime and size afterwards. The script under test gets the same
environment, so `LICHTHAUS_SOCK` points it at the test socket.
