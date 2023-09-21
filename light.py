from machine import Pin, SoftI2C
import neopixel
import utime

from umqtt.robust import MQTTClient

import _thread

STRIP_PIN = 16
NUM_LEDS = 30

white = (255, 255, 255, 0)
full_white = (255, 255, 255, 255)
off = (0, 0, 0, 0)

red = (255, 0, 0, 0)
green = (0, 255, 0, 0)
blue = (0, 0, 255, 0)
yellow = (255, 255, 0, 0)
purple = (255, 0, 255, 0)

sun = (255, 64, 0, 0)

class WakeUpLight:
    topics = ['sunrise', 'sunset', 'toggle', 'color']
    sunrise_seconds = 5 # default 20 minutes i.e. ~ 1200 seconds
    sunset_seconds = 5 # default 20 minutes i.e. ~ 1200 seconds
    
    light_status = 0 # by default at startup the light is off
    sunrise_status = 0
    sunset_status = 0
    
    def __init__(self, pin: int, num_leds: int, mqtt_client=None, topic_prefix='wakeuplight', bpp=4):
        self.np = neopixel.NeoPixel(
                                    pin=Pin(pin),
                                    n=num_leds,
                                    bpp=bpp
                                    )
        
        self.client = mqtt_client
        self.topic_prefix = topic_prefix
        
#         self.sunrise_status = 0
        
        self.start()
        # reset light to off
#         self.off()
    
    def start(self):
        self.off() if self.light_status == 0 else self.on()
        
        if self.client is not None:
            self.mqtt_connect()

    
    def mqtt_connect(self, timeout=5):
        '''
        Connect to mqtt broker
        Status:
            -1 >> not connected, first attempt
             1 >> connected
             0 >> not connected, timeout
        '''
        mqtt_status = -1
        self.client.set_callback(self.mqtt_cb)
        
        while mqtt_status < 0:
            for i in range(timeout):
#                 print(f'MQTT trial {i+1}')
                try:
                    self.client.connect()
                    mqtt_status = 1
                    for topic in self.topics:
                        self.client.subscribe(f'{self.topic_prefix}/{topic}')
                    break
                except:
                    print(f'Connecting to broker... trial {i+1}/{timeout}')
                    utime.sleep(10)
                    continue
            # if timeout, set mqtt_status
            if mqtt_status != 1:
                mqtt_status = 0
        
        print('Connected to mqtt broker' if mqtt_status == 1 else 'Error: cannot reach mqtt broker')
        
    def mqtt_cb(self, topic, msg):
        '''
        Callback function to operate the lamp based on mqtt messages
        '''
        full_topic = topic.decode('utf-8')
        msg = msg.decode('utf-8')
        
        topic = full_topic.split('/')[-1]
        
        if topic == 'sunrise':
            if msg == 'start':
                self.sunrise_status = 1
            elif msg == 'stop':
                self.sunrise_status = 0
#                 print(f'Full sunrise in {self.sunrise_seconds/60} minutes')
            print(f'Sunrise status: {self.sunrise_status}')
            #print(f'Sunrise run: {self.sunrise_run}')
            _thread.start_new_thread(self.sunrise, (self.sunrise_seconds, self.sunrise_status))
                #self.sunrise(self.sunrise_seconds)
#             elif msg == 'stop':
#                 self.sunrise_status = 0
#                 self.off()
#                 print('stop sunrise')
        
        elif topic == 'sunset':
            if msg == 'start':
                self.sunset_status = 1
                print(f'Full sunset in {self.sunrise_seconds/60} minutes')
                self.sunset(self.unset_seconds)
            elif msg == 'stop':
                self.sunset_status = 0
                self.off()
                print('stop sunset')
        
        elif topic == 'toggle':
            print('toggle', msg)
            if msg == '1':
                self.on() if self.light_status == 0 else self.off()
            elif msg == '0':
                self.off() if self.light_status == 1 else self.on()
        
        elif topic == 'color':
            print('Change color')
    
    
    def sunrise_run(self):
        run = self.sunrise_status
        return run
    
    
    def off(self):
        '''
        Turn the light off
        '''
        print('Turning light off')
        for led in range(self.np.n):
            self.np[led] = (0,0,0,0)
        self.np.write()
        
        self.light_status = 0
    
    
    def on(self, full=True):
        '''
        Turn the light on
        '''
        print('Turning light on')
        for led in range(self.np.n):
            self.np[led] = (255,255,255,255) if full else (255,255,255,0)
        self.np.write()
        
        self.light_status = 1
        
    
    def set_rgbw(self, color):
        '''
        Set the given color
        '''
        for led in range(self.np.n):
            self.np[led] = color
        self.np.write()
    
    
    def fade_in(self, led_n, color, seconds, steps=300):
        '''
        Fade in a given color
        '''
        delay = seconds / steps
        brightness = 0
        
        for step in range(steps + 1):
            # scale the brightness from 0 to 255
            brightness = int(step * 255 / steps)
            # set the led to the brightness for the given color
            self.np[led_n] = tuple(int(brightness * c / 255) for c in color)
            self.np.write()
            utime.sleep(delay)
        # set full brightness
        self.np[led_n] = color
        self.np.write()

    
    def fade_out(self, led_n, color, seconds, steps=300):
        '''
        Fade out a given color
        '''
        delay = seconds / steps
        brightness = 255
        
        self.np[led_n] = color
        self.np.write()
        
        for step in range(steps, -1, -1):
            # scale the brightness from 0 to 255
            brightness = int(step * 255 / steps)
            # set the led to the brightness for the given color
            self.np[led_n] = tuple(int(brightness * c / 255) for c in color)
            self.np.write()
            utime.sleep(delay)
        
    
    def transition(self, start_led, end_led, color, delay_ms=500, steps=1, fade=False):
        '''
        Turn on different leds at a given interval
        '''  
        for led in range(start_led, end_led, steps):
            if fade:
                self.fade_in(led, color, 5)
                utime.sleep_ms(delay_ms)
            else:
                self.np[led] = color
                self.np.write()
            
    
    def sunrise(self, seconds, status):
        '''
        Simulate sunrise
        '''
#         while self.sunrise_status == 1:
        while status == 1:
            print('Starting sunrise')
            sun_start = 1
            sun_end = self.np.n
            color = sun
            delay = seconds / self.np.n
            
            for led in range(sun_start, sun_end):
                self.fade_in(led, color, delay, steps=240)
            
            print('Sunrise completed')
            self.light_status = 1
            self.sunrise_status = 0
        
        print('Stopping sunrise')
        self.sunrise_status = 0
    
    
    def sunset(self, seconds):
        '''
        Simulate sunset
        '''
        while self.sunset_status == 1:
            print('Starting sunset')
            sun_start = self.np.n
            sun_end = 0
            color = sun
            # make sure the sun is on
            self.set_rgbw(color)
            
            delay = seconds / self.np.n
            
            for led in range(sun_start - 1, sun_end, -1):
                self.fade_out(led, color, delay, steps=240)
            
            print('Sunset completed')
            self.light_status = 0
            self.sunset_status = 0
        
        

# ### TESTING
# client_id = 'wakeuplight'
# broker = 'io.adafruit.com'
# port = 1883
# username = 'pl0s1'
# password = 'ee1f01b973f1c2ceb9c14b5f1d9be342e5484410'
# 
# mqtt_client = MQTTClient(client_id, broker, port, username, password, 60)
# 
# 
# l = WakeUpLight(STRIP_PIN, NUM_LEDS, mqtt_client)
# # l.fade_out(2, sun, 15)
# l.sunrise(15)
# l.sunset(15)
# # middle = STRIP_PIN // 2
# # l.transition(middle, NUM_LEDS, sun, fade=True)
# # l.fade_in(8, sun, 15)
# # utime.sleep_ms(250)
# l.on()
# utime.sleep_ms(500)
# l.on(full=False)
# utime.sleep_ms(1000)
# l.off()