import gc
gc.enable()
gc.collect()

import network
import utime
import uasyncio
import _thread
import dht
from machine import Pin
from mqtt_as import MQTTClient, config
from sunrise import NeoPixelAlarm
import ujson


class NeoPixelMQTT:
    topics = ['toggle_light', 'set_brightness', 'toggle_heartbeat', 'set_alarm_time',
              'set_rgbw', 'set_utc_offset', 'set_dst_offset', 'set_alarm_hour',
              'set_alarm_minute', 'set_alarm_delay', 'toggle_alarm', 'publish_updates']
    
    
    def __init__(self, neopixel_obj, dht_config: dict, btn_config: dict, mqtt_config: dict, wifi_config: dict):
        
        self.neo = neopixel_obj
        self.neo_alarm = NeoPixelAlarm(self.neo)
        
        config['client_id'] = mqtt_config['client_id']
        config['server'] = mqtt_config['broker']
        config['port'] = mqtt_config['port']
        config['user'] = mqtt_config['username']
        config['password'] = mqtt_config['password']
        config['queue_len'] = mqtt_config['queue_len']
        config['ssl'] = mqtt_config['ssl']
        config['ssl_params'] = mqtt_config['ssl_params']
        config['clean'] = mqtt_config['clean']
        
        config['ssid'] = wifi_config['ssid']
        config['wifi_pw'] = wifi_config['wifi_pw']
        
        self.topic_prefix = mqtt_config['topic_prefix']
        
        
        MQTTClient.DEBUG = True
        self.client = MQTTClient(config)
        
        self.dht_config = dht_config
        self.btn_config = btn_config
        self.dht = None
        self.btn = None
        self.dht_init()
        self.btn_init()
        
    
    async def publish_updates(self):
        try:
            await self.client.publish(f'{self.topic_prefix}/light_on', f'{self.neo.light_on}', qos=1)
            await self.client.publish(f'{self.topic_prefix}/alarm_on', f'{self.neo_alarm.alarm_on}', qos=1)
            await self.client.publish(f'{self.topic_prefix}/current_rgbw', f'{self.neo.current_color}', qos=1)
            await self.client.publish(f'{self.topic_prefix}/brightness', f'{self.neo.brightness}', qos=1)
            await self.client.publish(f'{self.topic_prefix}/alarm_delay', f'{self.neo_alarm.alarm_delay/60}', qos=1)
            await self.client.publish(f'{self.topic_prefix}/alarm_time', f'{self.neo_alarm.alarm_hour:02d}:{self.neo_alarm.alarm_minute:02d}', qos=1)
            await self.client.publish(f'{self.topic_prefix}/current_time', f'{utime.localtime()[3]:02d}:{utime.localtime()[4]:02d}', qos=1)
            await self.client.publish(f'{self.topic_prefix}/current_date', f'{utime.localtime()[2]:02d}/{utime.localtime()[1]:02d}/{utime.localtime()[0]}', qos=1)
            await self.client.publish(f'{self.topic_prefix}/timezone', f'{self.neo_alarm.utc_offset/3600} UTC (+ {self.neo_alarm.dst_offset/3600} DST)', qos=1)
        except OSError as e:
            await self.client.publish(f'{self.topic_prefix}/logs', f'{e}', qos=1)
    
    
    def save_to_config(self):
        res = {
            "sunrise_delay": self.neo_alarm.alarm_delay,
            "utc_offset": self.neo_alarm.utc_offset,
            "dst_offset": self.neo_alarm.dst_offset,
            "alarm_hour": self.neo_alarm.alarm_hour,
            "alarm_minute": self.neo_alarm.alarm_minute,
            "alarm_on": 1 if self.neo_alarm.alarm_on else 0
        }
        
        try:
            with open('config.json', 'w') as f:
                ujson.dump(res, f)
        except OSError as e:
            print(f'Error saving configuration: {e}')
        
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
    
       
    async def send_updates(self, delay:float):
        '''
        Call the publish_updates function at a given interval to periodically
        publish updates to all topics
        '''
        while True:
            uasyncio.create_task(self.publish_updates())
            await uasyncio.sleep(delay)
    
    async def mqtt_connect(self):
        '''
        Main function to start a connection and events loop
        '''
        await self.client.connect()
        for coroutine in (self.up, self.messages):
            uasyncio.create_task(coroutine())
        while True:
            await uasyncio.sleep(0)
   
    async def messages(self):
        '''
        Handle incoming messages
        '''
        async for topic, msg, retained in self.client.queue:
            topic = topic.decode('utf-8')
            msg = msg.decode('utf-8')
            
            print(f'topic: {topic} -- message: {msg}')
            
            if topic == f'{self.topic_prefix}/toggle_light':
                self.neo.toggle()
                uasyncio.create_task(self.publish_updates())
            
            elif topic == f'{self.topic_prefix}/set_brightness':
                self.neo.set_brightness(float(msg))
                uasyncio.create_task(self.publish_updates())
            
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
                uasyncio.create_task(self.publish_updates())
            
            elif topic == f'{self.topic_prefix}/set_utc_offset':
                self.neo_alarm.utc_offset = int(msg) * 3600
                uasyncio.create_task(self.publish_updates())
                self.save_to_config()
            
            elif topic == f'{self.topic_prefix}/set_dst_offset':
                self.neo_alarm.dst_offset = int(msg) * 3600
                uasyncio.create_task(self.publish_updates())
                self.save_to_config()
            
            elif topic == f'{self.topic_prefix}/set_alarm_time':
                self.neo_alarm.alarm_hour = int(msg.split(':')[0])
                self.neo_alarm.alarm_minute = int(msg.split(':')[1])
                uasyncio.create_task(self.publish_updates())
                self.save_to_config()
                
            elif topic == f'{self.topic_prefix}/set_alarm_hour':
                self.neo_alarm.alarm_hour = int(msg)
                uasyncio.create_task(self.publish_updates())
                self.save_to_config()
                
            elif topic == f'{self.topic_prefix}/set_alarm_minute':
                self.neo_alarm.alarm_minute = int(msg)
                uasyncio.create_task(self.publish_updates())
                self.save_to_config()
            
            elif topic == f'{self.topic_prefix}/set_alarm_delay':
                self.neo_alarm.alarm_delay = int(msg) * 60
                uasyncio.create_task(self.publish_updates())
                self.save_to_config()
            
            elif topic == f'{self.topic_prefix}/toggle_alarm':
                self.neo_alarm.alarm_on = False if self.neo_alarm.alarm_on else True
                uasyncio.create_task(self.publish_updates())
                self.save_to_config()
            
            elif topic == f'{self.topic_prefix}/publish_updates':
                self.neo_alarm.update_time()
                uasyncio.create_task(self.publish_updates())
    
    async def up(self):
        '''
        Subscribe to topics
        '''
        while True:
            await self.client.up.wait()
            self.client.up.clear()
            await self.client.subscribe(f'{self.topic_prefix}/#', qos=1)
#             for topic in NeoPixelMQTT.topics:
#                 await self.client.subscribe(f'{self.topic_prefix}/{topic}', qos=1)

    
    async def mqtt_heartbeat(self, delay: float):
        '''
        Publsh mqtt heartbeat
        '''
        while True:
            await self.client.publish(f'{self.topic_prefix}/heartbeat', 'beat', qos=1)
            await uasyncio.sleep(delay)
    
    async def send_dht(self, delay: float):
        '''
        Periodically publish DHT updates
        '''
        while True:
            self.dht.measure()
            await self.client.publish(f'{self.topic_prefix}/temp', f'{self.dht.temperature()}', qos=1)
            await self.client.publish(f'{self.topic_prefix}/hum', f'{self.dht.humidity()}', qos=1)
            await uasyncio.sleep(delay)
