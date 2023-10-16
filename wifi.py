from wifi_manager import WifiManager
import utime

AP_SSID = 'Wake Up Light'
AP_PWD = 'wakeuplight'
HOSTNAME = 'wakeuplight'

wm = WifiManager(ssid=AP_SSID, password=AP_PWD, reboot=True, debug=False, hostname=HOSTNAME)

def do_connect(webrepl_run=False):
#     wm = WifiManager(ssid=AP_SSID, password=AP_PWD, reboot=True, debug=False, hostname=HOSTNAME)
    wm.disconnect()
    utime.sleep_ms(250)
    wm.connect()
    while True:
        if wm.is_connected():
            print('\nConnected!')
            utime.sleep_ms(250) # wait to get network details
            if webrepl_run:
                import webrepl
                webrepl.start()
            return True
        else:
            print('\nDisconnected!')
        utime.sleep(5)
    return False

def do_disconnect():
    wm.disconnect()