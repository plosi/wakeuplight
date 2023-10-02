# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()

from wifi import do_connect

try:
    is_wifi_connected = do_connect()
except:
    print('Error: no wifi connectivity')