import gc
gc.enable()
gc.collect()

import network
import utime
import json
import uasyncio
import _thread
import dht
from machine import Pin
from umqtt.robust import MQTTClient
from sunrise import NeoPixelAlarm


class NeoPixelMQTT:
    topics = ['toggle_light', 'set_brightness', 'toggle_heartbeat', 'set_alarm_time',
              'set_rgbw', 'set_utc_offset', 'set_dst_offset', 'set_alarm_hour',
              'set_alarm_minute', 'set_alarm_delay', 'toggle_alarm']
    
    def __init__(self, neopixel_obj,
#                  neopixel_alarm_obj,
                 dht_config: dict, btn_config: dict, mqtt_config: dict):
        self.neo = neopixel_obj
        self.neo_alarm = NeoPixelAlarm(self.neo)#neopixel_alarm_obj
        
        self.client_id = mqtt_config['client_id']
        self.broker = mqtt_config['broker']
        self.port = mqtt_config['port']
        self.username = mqtt_config['username']
        self.password = mqtt_config['password']
        self.topic_prefix = mqtt_config['topic_prefix']
        self.ssl_params = mqtt_config['ssl_params']
        
        self.client = MQTTClient(self.client_id, self.broker, self.port, self.username, self.password, ssl=True, ssl_params=self.ssl_params, keepalive=60)
        
        self.dht_config = dht_config
        self.btn_config = btn_config
        self.dht = None
        self.btn = None
        self.dht_init()
        self.btn_init()
    
    def publish_updates(self):
        try:
            self.client.publish(f'{self.topic_prefix}/light_on', f'{self.neo.light_on}', qos=0)
            self.client.publish(f'{self.topic_prefix}/alarm_on', f'{self.neo_alarm.alarm_on}', qos=0)
            self.client.publish(f'{self.topic_prefix}/current_rgbw', f'{self.neo.current_color}', qos=0)
            self.client.publish(f'{self.topic_prefix}/brightness', f'{self.neo.brightness}', qos=0)
            self.client.publish(f'{self.topic_prefix}/alarm_time', f'{self.neo_alarm.alarm_hour:02d}:{self.neo_alarm.alarm_minute:02d}', qos=0)
            self.client.publish(f'{self.topic_prefix}/current_time', f'{utime.localtime()[3]:02d}:{utime.localtime()[4]:02d}', qos=0)
            self.client.publish(f'{self.topic_prefix}/current_date', f'{utime.localtime()[2]:02d}/{utime.localtime()[1]:02d}/{utime.localtime()[0]}', qos=0)
            self.client.publish(f'{self.topic_prefix}/timezone', f'{self.neo_alarm.utc_offset/3600} UTC (+ {self.neo_alarm.dst_offset/3600} DST)', qos=0)
        except OSError as e:
            self.client.publish(f'{self.topic_prefix}/logs', f'{e}', qos=0)
        
        
    def dht_init(self):
        print('Initializing DHT sensor...')
        
        gnd = Pin(self.dht_config['dht_gnd'], Pin.OUT)
        vcc = Pin(self.dht_config['dht_vcc'], Pin.OUT)
        self.dht = dht.DHT22(Pin(self.dht_config['dht_pin']))
        
        gnd.off()
        vcc.on()
    
    def btn_init(self):
        print('Initializing BTN...')
        
        self.btn = Pin(self.btn_config['btn_pin'], Pin.IN, Pin.PULL_UP)
    
    def set_cb(self):
        self.client.set_callback(self.mqtt_cb)
       
    async def send_updates(self, delay:float):
        while True:
            self.publish_updates()
            await uasyncio.sleep(delay)
    
    async def mqtt_connect(self):
        reconnect = True
        while reconnect:
            try:
                self.client.connect()
                reconnect = False
            except OSError as e:
                print(f'Error {e.errno}: {e}')
                print(f'Connecting to {self.broker}...')
                return
                await uasyncio.sleep(10)
        print(f'Connected to {self.broker}')
        print('Subscribing...')
        for topic in NeoPixelMQTT.topics:
            self.client.subscribe(f'{self.topic_prefix}/{topic}')
            utime.sleep(0.1)
        print('Sending updates...')
        self.publish_updates()
   
    def mqtt_cb(self, topic, msg):
        topic = topic.decode('utf-8')
        msg = msg.decode('utf-8')
        
        print(f'topic: {topic} -- message: {msg}')
        
        if topic == f'{self.topic_prefix}/toggle_light':
            self.neo.toggle()
            self.publish_updates()
        
        elif topic == f'{self.topic_prefix}/set_brightness':
            self.neo.set_brightness(float(msg))
            self.publish_updates()
        
        elif topic == f'{self.topic_prefix}/toggle_heartbeat':
            self.neo.heartbeat_on = False if self.neo.heartbeat_on else True
        
        elif topic == f'{self.topic_prefix}/set_rgbw':
            if '#' in msg:
                hex = msg.lstrip('#')
                r, g, b = tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))
            else:
                msg = msg.split('rgb')[1]
                msg = msg.lstrip('(').strip(')')
                msg = msg.split(',')
                r = int(msg[0])
                g = int(msg[1])
                b = int(msg[2])
            color = (r,g,b,0)
            self.neo.change_color(color)
            self.publish_updates()
        
        elif topic == f'{self.topic_prefix}/set_utc_offset':
            self.neo_alarm.utc_offset = int(msg) * 3600
            self.publish_updates()
        
        elif topic == f'{self.topic_prefix}/set_dst_offset':
            self.neo_alarm.dst_offset = int(msg) * 3600
            self.publish_updates()
        
        elif topic == f'{self.topic_prefix}/set_alarm_time':
            self.neo_alarm.alarm_hour = int(msg.split(':')[0])
            self.neo_alarm.alarm_minute = int(msg.split(':')[1])
            self.publish_updates()
            
        elif topic == f'{self.topic_prefix}/set_alarm_hour':
            self.neo_alarm.alarm_hour = int(msg)
            self.publish_updates()
            
        elif topic == f'{self.topic_prefix}/set_alarm_minute':
            self.neo_alarm.alarm_minute = int(msg)
            self.publish_updates()
        
        elif topic == f'{self.topic_prefix}/set_alarm_delay':
            self.neo_alarm.alarm_delay = int(msg)
            self.publish_updates()
        
        elif topic == f'{self.topic_prefix}/toggle_alarm':
            self.neo_alarm.alarm_on = False if self.neo_alarm.alarm_on else True
            self.publish_updates()
        
        elif topic == f'{self.topic_prefix}/publish_updates':
            self.publish_updates()
        
    def mqtt_isconnected(self):
        try:
            self.client.ping()
            self.client.ping()
        except:
            print('MQTT disconnected')
            return False
        else:
            return True
    
    async def _check_isconnected(self, delay: float):
        while True:
            if not self.mqtt_isconnected():
                uasyncio.create_task(self.mqtt_connect())
            await uasyncio.sleep(delay)
    
    async def _check_msg(self):
        while True:
            self.client.check_msg()
            await uasyncio.sleep(1)
    
    async def mqtt_heartbeat(self, delay: float):
        while True:
            self.client.publish(f'{self.topic_prefix}/heartbeat', 'beat', qos=0)
            await uasyncio.sleep(delay)
    
    async def send_dht(self, delay: float):
        while True:
            self.dht.measure()
            self.client.publish(f'{self.topic_prefix}/temp', f'{self.dht.temperature()}', True)
            self.client.publish(f'{self.topic_prefix}/hum', f'{self.dht.humidity()}', True)
            await uasyncio.sleep(delay)
