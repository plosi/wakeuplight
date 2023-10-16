import gc
gc.enable()
gc.collect()

import uasyncio
import ujson

from light import NeoPixelLight
from sunrise import NeoPixelAlarm
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
try:
    with open('wifi_config.json', 'r') as f:
        tmp = ujson.load(f)
        wifi_config = {'ssid': tmp['ssid'], 'wifi_pw': tmp['wifi_pw']}
except OSError as e:
    print(f'Cannot open wifi config file: {e}')


if __name__ == '__main__':
    neo = NeoPixelLight(STRIP_PIN, NUM_LEDS)
    neo_mqtt = NeoPixelMQTT(neo,
                            dht_config=dht_config,
                            btn_config=btn_config,
                            mqtt_config=mqtt_config,
                            wifi_config=wifi_config)
    
    if start:
        gc.collect()
        ## alarm
        uasyncio.create_task(neo_mqtt.neo_alarm.call_update_time(3600))
        uasyncio.create_task(neo_mqtt.neo_alarm.check_for_alarm(0.5))
        
        ## light
        uasyncio.create_task(neo_mqtt.neo.start_heartbeat())
        
        ## mqtt
        uasyncio.create_task(neo_mqtt.mqtt_heartbeat(60))
        uasyncio.create_task(neo_mqtt.send_dht(900))
        uasyncio.create_task(neo_mqtt.send_updates(3600))
        
        try:
            gc.collect()
            uasyncio.run(neo_mqtt.mqtt_connect())
        finally:
            gc.collect()
            neo_mqtt.client.close()
            uasyncio.new_event_loop()
        
        
