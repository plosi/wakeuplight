# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()

from wifi import do_connect, do_disconnect

start = False

try:
    is_wifi_connected = do_connect(webrepl_run=False)
    print('Wifi configuration saved, disconnecting now...')
    start = True
    do_disconnect()
except:
    print('Error: no wifi connectivity')
    