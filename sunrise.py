import gc
gc.enable()
gc.collect()

import utime
import uasyncio
import ntptime
import urequests
from machine import RTC
import ujson

class NeoPixelAlarm:
    
    def __init__(self, neopixel_obj):
        self.neo = neopixel_obj
        
        try:
            with open('config.json', 'r') as f:
                c = ujson.load(f)
                self.utc_offset = c['utc_offset']
                self.dst_offset = c['dst_offset']
                self.alarm_hour = c['alarm_hour']
                self.alarm_minute = c['alarm_minute']
                self.alarm_delay = c['sunrise_delay']
                self.alarm_on = True if c['alarm_on'] == 1 else False
                
        except OSError as e:
            print(f'Error alarm configs: {e}')
            self.utc_offset = 3600
            self.dst_offset = 0  
            self.alarm_hour = 6
            self.alarm_minute = 15
            self.alarm_delay = 1200.0
            self.alarm_on = True
        
        self.alarm_running = False

    def update_time(self):
        '''
        Update the local time via internet
        '''
        try:
            response = urequests.get('http://worldtimeapi.org/api/ip')
            if response.status_code == 200:
                print('API time updated')
                parsed = response.json()
                self.utc_offset = parsed['raw_offset']
                self.dst_offset = parsed['dst_offset']
                dt = utime.localtime(parsed['unixtime'] + self.utc_offset + self.dst_offset - 946684800)
        except:
            try:
                ntptime.settime()
                dt = utime.localtime(utime.mktime(utime.localtime()) + self.utc_offset + self.dst_offset)
                print('NTP time updated')
            except:
                print('Impossible to update time: no connection?')
                dt = utime.gmtime(utime.time() + self.utc_offset + self.dst_offset)
        
        # save updated time as localtime
        RTC().datetime((dt[0], dt[1], dt[2], dt[6] + 1, dt[3], dt[4], dt[5], 0))
        print(dt)

    async def call_update_time(self, delay=300):
        '''
        Async function to call update_time every 'delay' seconds
        '''
        while True:
            self.update_time()
            await uasyncio.sleep(delay)
    
    async def check_for_alarm(self, delay=.5):
        '''
        Async function to check when it is time to trigger the alarm
        '''        
        while True:
            now_hr = utime.localtime()[3]
            now_mn = utime.localtime()[4]
            
            if self.alarm_on:
                if (now_hr == self.alarm_hour) & (now_mn == self.alarm_minute) & (self.alarm_running is not True):
                    self.alarm_running = True
                    uasyncio.create_task(self.neo.sunrise(delay=self.alarm_delay))
                # reset the alarm_run flag once the alarm is terminated
                elif self.alarm_running:
                    if (now_hr >= self.alarm_hour) & (now_mn > (self.alarm_minute + self.alarm_delay / 60)):
                        self.alarm_running = False
            
            await uasyncio.sleep(delay)
            