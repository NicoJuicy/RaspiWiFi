import RPi.GPIO as GPIO
import os
import re
import time
import subprocess
import reset_lib

def get_serial():
    pattern = r'^Serial\s*:\s*(\w+)$'
    cpuinfo = subprocess.check_output(['cat', '/proc/cpuinfo']).decode()
    lines = cpuinfo.split('\n')

    for line in lines:
        match = re.match(pattern, line.strip())
        if not match:
            continue
        return match.group(1)

    return ''


GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

counter = 0
serial_last_four = get_serial()
serial_last_four = ' ' + serial_last_four[-4:] if len(serial_last_four) > 4 else serial_last_four  # get last 4 characters of serial
config_hash = reset_lib.config_file_hash()
ssid_prefix = config_hash['ssid_prefix']
reboot_required = False


reboot_required = reset_lib.wpa_check_activate(config_hash['wpa_enabled'], config_hash['wpa_key'])

reboot_required = reset_lib.update_ssid(ssid_prefix, serial_last_four='')

if reboot_required == True:
    os.system('reboot')

# This is the main logic loop waiting for a button to be pressed on GPIO 18 for 10 seconds.
# If that happens the device will reset to its AP Host mode allowing for reconfiguration on a new network.
while True:
    while GPIO.input(18) == 1:
        time.sleep(1)
        counter = counter + 1

        print(counter)

        if counter == 9:
            reset_lib.reset_to_host_mode()

        if GPIO.input(18) == 0:
            counter = 0
            break

    time.sleep(1)
