import gc
gc.enable()
gc.collect()

import uasyncio
import _thread

from light import NeoPixelLight
from sunrise import NeoPixelAlarm
# from webserver import NeoPixelConnect
from mqtt import NeoPixelMQTT

STRIP_PIN = 16
NUM_LEDS = 30

dht_config = {
    'dht_pin': 13,
    'dht_vcc': 12,
    'dht_gnd': 14
    }

btn_config = {
    'btn_pin': 0
    }

from secrets import mqtt_config

######################
### Task Scheduler ###
######################

# tasks/coroutines
async def coroutines():
    gc.collect()
    # webserver
#     uasyncio.create_task(neo_web.start_server())
    
    ## alarm
    uasyncio.create_task(neo_mqtt.neo_alarm.call_update_time(300))
    uasyncio.create_task(neo_mqtt.neo_alarm.check_for_alarm(0.2))
    
    ## light
    uasyncio.create_task(neo_mqtt.neo.start_heartbeat())
    
    ## mqtt
    uasyncio.create_task(neo_mqtt.mqtt_connect())
    uasyncio.create_task(neo_mqtt._check_msg())
    uasyncio.create_task(neo_mqtt._check_isconnected(120))
    uasyncio.create_task(neo_mqtt.mqtt_heartbeat(60))
    uasyncio.create_task(neo_mqtt.send_dht(900))
    uasyncio.create_task(neo_mqtt.send_updates(60))
    
    while True:
        await uasyncio.sleep(0)

# async def second_thread_coroutines():
#     gc.collect()
#     uasyncio.create_task(neo_mqtt._check_msg())
#     uasyncio.create_task(neo_mqtt.send_dht(120))
#     
#     while True:
#         await uasyncio.sleep(0)

def mqtt_tasks():
    neo_mqtt.set_cb()
#     uasyncio.create_task(neo_mqtt.mqtt_connect())

#     uasyncio.run(coroutines())


### MAIN ###

if __name__ == '__main__':
    neo = NeoPixelLight(STRIP_PIN, NUM_LEDS)
#     neo_alarm = NeoPixelAlarm(neo)
#     neo_web = NeoPixelConnect(neo, neo_alarm, dht_config, btn_config)
    neo_mqtt = NeoPixelMQTT(neo,
#                             neo_alarm,
                            dht_config=dht_config, btn_config=btn_config, mqtt_config=mqtt_config)

    if is_wifi_connected:
        _thread.start_new_thread(mqtt_tasks, ())
        uasyncio.run(coroutines())
        
        
