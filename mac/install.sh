#!/bin/bash
# Installs the tool into ~/DesktopToDrive and the app into /Applications.
# Automatic moving stays OFF until you choose "Turn on" in the app.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
DIR="$HOME/DesktopToDrive"
mkdir -p "$DIR"
cp "$HERE/../move.py" "$HERE/start.sh" "$HERE/stop.sh" "$DIR/"
chmod +x "$DIR/move.py" "$DIR/start.sh" "$DIR/stop.sh"
[ -f "$DIR/keep.txt" ] || printf '# Names of Desktop items to keep (one per line)\n' > "$DIR/keep.txt"
# Not turned on yet: make sure nothing moves by itself
[ -f "$HOME/Library/LaunchAgents/com.desktop-to-drive.plist" ] || touch "$DIR/PAUSE"
"$HERE/build-app.sh"
echo "Installed in $DIR. Open \"Desktop to Drive\" from Applications."
