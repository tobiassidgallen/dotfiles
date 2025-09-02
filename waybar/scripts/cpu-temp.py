#!/usr/bin/env python3
import subprocess
import json
import sys

def get_cpu_temp():
    try:
        # Get temperature from sensors
        result = subprocess.run(['sensors'], capture_output=True, text=True, check=True)
        
        # Parse temperature (looking for temp1 like your original command)
        for line in result.stdout.split('\n'):
            if 'temp1' in line:
                # Extract temperature value
                temp_str = line.split()[1]
                # Remove °C and + signs, get just the number
                temp = float(temp_str.replace('+', '').replace('°C', ''))
                return int(temp)
        
        # Fallback: try to find any temperature reading
        for line in result.stdout.split('\n'):
            if '°C' in line and ('Core' in line or 'temp' in line):
                temp_str = line.split()[1] if len(line.split()) > 1 else line.split()[0]
                temp = float(temp_str.replace('+', '').replace('°C', ''))
                return int(temp)
                
        return None
        
    except (subprocess.CalledProcessError, ValueError, IndexError):
        return None

def main():
    temp = get_cpu_temp()
    
    if temp is None:
        # Fallback output
        print(json.dumps({
            "text": "N/A°C",
            "class": "unknown",
            "tooltip": "Temperature unavailable"
        }))
        return
    
    # Determine CSS class based on temperature ranges
    # Green = Below 40°C, Yellow = 40-59°C, Orange = 60-79°C, Red = 80°C+
    if temp < 40:
        css_class = "excellent"
        status = "Excellent"
    elif temp < 60:
        css_class = "good" 
        status = "Good"
    elif temp < 80:
        css_class = "warning"
        status = "Warning"
    else:
        css_class = "critical"
        status = "Critical"
    
    # Output JSON for waybar
    output = {
        "text": f"{temp}°C",
        "class": css_class,
        "tooltip": f"CPU Temperature: {temp}°C ({status})"
    }
    
    print(json.dumps(output))

if __name__ == "__main__":
    main()
