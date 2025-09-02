#!/usr/bin/env python3
import subprocess
import json
import sys
import re

def get_wifi_info():
    try:
        # First try: nmcli for NetworkManager systems
        result = subprocess.run(['nmcli', '-t', '-f', 'ACTIVE,SSID,SIGNAL', 'dev', 'wifi'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.startswith('yes:'):  # Active connection marked with yes:
                    parts = line.split(':')
                    if len(parts) >= 3:
                        ssid = parts[1].strip()
                        signal_str = parts[2].strip()
                        if signal_str.isdigit():
                            return ssid, int(signal_str)
        
        # Second try: iwconfig for older systems
        result = subprocess.run(['iwconfig'], capture_output=True, text=True)
        
        if result.returncode == 0:
            current_interface = None
            ssid = None
            signal = None
            
            for line in result.stdout.split('\n'):
                # Look for wireless interface
                if re.match(r'^[a-zA-Z0-9]+\s+IEEE 802.11', line):
                    current_interface = line.split()[0]
                
                # Look for ESSID in current interface
                if current_interface and 'ESSID:' in line:
                    essid_match = re.search(r'ESSID:"([^"]*)"', line)
                    if essid_match and essid_match.group(1) != 'off/any':
                        ssid = essid_match.group(1)
                
                # Look for signal level
                if current_interface and 'Signal level=' in line:
                    signal_match = re.search(r'Signal level=(-?\d+)', line)
                    if signal_match:
                        dbm = int(signal_match.group(1))
                        # Convert dBm to percentage
                        if dbm <= -100:
                            signal = 0
                        elif dbm >= -50:
                            signal = 100
                        else:
                            signal = 2 * (dbm + 100)
                        break
            
            if ssid and signal is not None:
                return ssid, signal
        
        # Third try: check /proc/net/wireless
        try:
            with open('/proc/net/wireless', 'r') as f:
                lines = f.readlines()
                for line in lines[2:]:  # Skip header lines
                    parts = line.split()
                    if len(parts) >= 3:
                        interface = parts[0].rstrip(':')
                        # Get SSID for this interface
                        ssid_result = subprocess.run(['iwgetid', interface, '-r'], 
                                                   capture_output=True, text=True)
                        if ssid_result.returncode == 0 and ssid_result.stdout.strip():
                            ssid = ssid_result.stdout.strip()
                            # Parse signal strength (usually in dBm)
                            try:
                                signal_val = float(parts[2])
                                if signal_val < 0:  # dBm value
                                    signal = max(0, min(100, 2 * (signal_val + 100)))
                                else:  # Already a percentage or quality
                                    signal = min(100, signal_val)
                                return ssid, int(signal)
                            except ValueError:
                                pass
        except FileNotFoundError:
            pass
        
        return None, None
        
    except Exception as e:
        return None, None

def check_internet():
    try:
        # Quick connectivity check
        result = subprocess.run(['ping', '-c', '1', '-W', '1', '1.1.1.1'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def get_ip_info():
    try:
        # Get IP address info
        result = subprocess.run(['ip', 'route', 'get', '1.1.1.1'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            # Look for the source IP
            for line in result.stdout.split('\n'):
                if 'src' in line:
                    parts = line.split()
                    src_index = parts.index('src')
                    if src_index + 1 < len(parts):
                        return parts[src_index + 1]
        return None
    except:
        return None

def main():
    ssid, signal = get_wifi_info()
    has_internet = check_internet()
    ip = get_ip_info()
    
    # Check if we're connected via ethernet (no wifi but have internet)
    if not ssid and has_internet and ip:
        output = {
            "text": f"󰈀 {ip}",
            "class": "ethernet",
            "tooltip": f"Wired connection\nIP: {ip}"
        }
        print(json.dumps(output))
        return
    
    # No connection at all
    if not ssid and not has_internet:
        output = {
            "text": "󰤭 OFFLINE",
            "class": "disconnected",
            "tooltip": "No network connection"
        }
        print(json.dumps(output))
        return
    
    # WiFi connection
    if ssid:
        if signal is None:
            signal = 50  # Default if we can't get signal strength
        
        # Determine CSS class and icon based on signal strength
        if signal >= 76:
            css_class = "excellent"
            status = "Excellent"
            icon = "󰤨"
        elif signal >= 51:
            css_class = "good"
            status = "Good"
            icon = "󰤥"
        elif signal >= 26:
            css_class = "fair"
            status = "Fair"
            icon = "󰤢"
        else:
            css_class = "weak"
            status = "Weak"
            icon = "󰤟"
        
        # Add connection status to tooltip
        connection_status = "Connected" if has_internet else "Limited connectivity"
        
        output = {
            "text": f"{icon} {signal}% {ssid}",
            "class": css_class,
            "tooltip": f"WiFi: {ssid}\nSignal: {signal}% ({status})\nStatus: {connection_status}"
        }
        print(json.dumps(output))
        return
    
    # Fallback - something is wrong
    output = {
        "text": "󰤭 ERROR",
        "class": "disconnected",
        "tooltip": "Network detection failed"
    }
    print(json.dumps(output))

if __name__ == "__main__":
    main()
