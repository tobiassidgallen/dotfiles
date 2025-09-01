#!/bin/bash
choice=$(echo -e "🔒 Lock\n💤 Sleep\n⏻ Shutdown\n🔄 Restart" | wofi --dmenu --prompt "Power:")
# Exit if no choice made (user canceled)
[ -z "$choice" ] && exit 0
case "$choice" in
    "🔒 Lock") swaylock -f -c 000000 -i ~/Pictures/wallpapers/lockscreen.jpg --show-failed-attempts --show-keyboard-layout --indicator-caps-lock ;;
    "💤 Sleep") systemctl suspend ;;
    "⏻ Shutdown") systemctl poweroff ;;
    "🔄 Restart") systemctl reboot ;;
    *) exit 1 ;;
esac
