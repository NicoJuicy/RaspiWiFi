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


def eth_is_set_up(interface):
    try:
        subprocess.check_output(['cat', f'/sys/class/net/{interface}/carrier'])
        return True
    except subprocess.CalledProcessError:
        return False


def eth_cable_connected(interface):
    try:
        carrier = subprocess.check_output(['cat', f'/sys/class/net/{interface}/carrier']).decode()
        connected = int(carrier)
        return connected == 1
    except subprocess.CalledProcessError:
        print('Interface rather not found:', interface)
        return False
    except ValueError:
        print('Invalid carrier value', carrier)
        return False


def wait_for_eth_wired(interface):
    seconds = 0
    while not eth_is_set_up(interface):
        time.sleep(1)
        seconds += 1
        if seconds >= 3:
            print('Timeout on eth interface: ', interface)
            return False

    return eth_cable_connected(interface)


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

if reset_lib.is_host_mode():
    wired = wait_for_eth_wired('eth0')
    if wired:
        reset_lib.set_ap_client_mode()

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
