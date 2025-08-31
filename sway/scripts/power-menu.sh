#!/bin/bash
choice=$(echo -e "Lock\nSleep\nShutdown\nRestart" | wofi --dmenu --prompt "Power:")
case "$choice" in
    Lock) swaylock -f -c 000000 -i ~/Pictures/wallpapers/lockscreen.jpg --show-failed-attempts --show-keyboard-layout --indicator-caps-lock ;;
    Sleep) systemctl suspend ;;
    Shutdown) systemctl poweroff ;;
    Restart) systemctl reboot ;;
esac
