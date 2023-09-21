from wifi_manager import WifiManager
import utime

AP_SSID = 'Wake Up Light'
AP_PWD = 'wakeuplight'

wm = WifiManager(ssid=AP_SSID, password=AP_PWD, reboot=True, debug=False)
# wm.connect()

def connect():
    wm.connect()
#     while True:
    for _ in range(6):
        if wm.is_connected():
            print('Connected!')
            return True
        else:
            print('Disconnected!')
        utime.sleep(5)
    
    return False

def disconnect():
    wm.disconnect()