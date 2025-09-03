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

def check_ethernet_connection():
    """Check if we have an active ethernet connection"""
    try:
        # Method 1: Check nmcli for ethernet connections
        result = subprocess.run(['nmcli', '-t', '-f', 'TYPE,STATE', 'connection', 'show', '--active'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line.startswith('ethernet:activated') or '802-3-ethernet:activated' in line:
                    return True
        
        # Method 2: Check network interfaces for active ethernet
        result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                # Look for ethernet interfaces that are UP
                if re.search(r'^[0-9]+:\s+(eth|eno|enp|ens)[^:]*:.*state UP', line):
                    return True
                # Also check for common ethernet interface patterns
                if re.search(r'^[0-9]+:\s+[^:]*:\s.*<.*UP.*>.*state UP', line) and 'wl' not in line and 'lo' not in line:
                    return True
        
        # Method 3: Check /sys/class/net for active ethernet interfaces
        import os
        net_path = '/sys/class/net'
        if os.path.exists(net_path):
            for interface in os.listdir(net_path):
                if interface.startswith(('eth', 'eno', 'enp', 'ens')):
                    # Check if interface is up
                    operstate_path = f"{net_path}/{interface}/operstate"
                    if os.path.exists(operstate_path):
                        try:
                            with open(operstate_path, 'r') as f:
                                if f.read().strip() == 'up':
                                    return True
                        except:
                            pass
        
        return False
        
    except Exception as e:
        return False

def check_internet():
    """Quick internet connectivity check"""
    try:
        result = subprocess.run(['ping', '-c', '1', '-W', '2', '1.1.1.1'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def get_ip_info():
    """Get current IP address"""
    try:
        # Method 1: Get default route IP
        result = subprocess.run(['ip', 'route', 'get', '1.1.1.1'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'src' in line:
                    parts = line.split()
                    try:
                        src_index = parts.index('src')
                        if src_index + 1 < len(parts):
                            return parts[src_index + 1]
                    except ValueError:
                        pass
        
        # Method 2: Get IP from active interfaces
        result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                # Look for inet addresses that aren't loopback
                if 'inet ' in line and '127.0.0.1' not in line:
                    match = re.search(r'inet\s+([0-9.]+)', line)
                    if match:
                        return match.group(1)
        
        return None
    except:
        return None

def get_ethernet_interface():
    """Get the name of the active ethernet interface"""
    try:
        result = subprocess.run(['ip', 'route', 'get', '1.1.1.1'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'dev' in line:
                    parts = line.split()
                    try:
                        dev_index = parts.index('dev')
                        if dev_index + 1 < len(parts):
                            interface = parts[dev_index + 1]
                            # Check if it's an ethernet interface
                            if interface.startswith(('eth', 'eno', 'enp', 'ens')):
                                return interface
                    except ValueError:
                        pass
        return None
    except:
        return None

def main():
    ssid, signal = get_wifi_info()
    has_internet = check_internet()
    ip = get_ip_info()
    has_ethernet = check_ethernet_connection()
    ethernet_interface = get_ethernet_interface()
    
    # Debug: If we have an IP but no detected internet, assume we have internet
    # This handles cases where ping/curl fails due to firewall but connection works
    if ip and not has_internet:
        has_internet = True
    
    # Priority 1: WiFi connection (if active)
    if ssid and signal is not None:
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
        
        connection_status = "Connected" if has_internet else "Limited connectivity"
        
        output = {
            "text": f"{icon} {signal}% {ssid}",
            "class": css_class,
            "tooltip": f"WiFi: {ssid}\nSignal: {signal}% ({status})\nStatus: {connection_status}" + (f"\nIP: {ip}" if ip else "")
        }
        print(json.dumps(output))
        return
    
    # Priority 2: We have an IP address, assume working connection
    if ip and has_internet:
        # Try to determine if it's ethernet
        if has_ethernet or ethernet_interface:
            interface_info = f" ({ethernet_interface})" if ethernet_interface else ""
            output = {
                "text": f"󰈀 Ethernet{interface_info}",
                "class": "ethernet",
                "tooltip": f"Wired connection{interface_info}\nIP: {ip}\nStatus: Connected"
            }
        else:
            # Generic connection
            output = {
                "text": f"󰈀 Connected",
                "class": "ethernet",
                "tooltip": f"Network connection\nIP: {ip}\nStatus: Connected"
            }
        print(json.dumps(output))
        return
    
    # Priority 3: We have an IP but limited internet
    if ip and not has_internet:
        if has_ethernet or ethernet_interface:
            interface_info = f" ({ethernet_interface})" if ethernet_interface else ""
            output = {
                "text": f"󰈀 Limited{interface_info}",
                "class": "disconnected",
                "tooltip": f"Ethernet connected{interface_info}\nIP: {ip}\nStatus: Limited connectivity"
            }
        else:
            output = {
                "text": f"󰈀 Limited",
                "class": "disconnected",
                "tooltip": f"Network connection\nIP: {ip}\nStatus: Limited connectivity"
            }
        print(json.dumps(output))
        return
    
    # Priority 4: No IP, no connection
    output = {
        "text": "󰤭 OFFLINE",
        "class": "disconnected",
        "tooltip": "No network connection"
    }
    print(json.dumps(output))

if __name__ == "__main__":
    main()
