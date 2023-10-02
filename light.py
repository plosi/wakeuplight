import gc
gc.enable()
gc.collect()

from machine import Pin
import neopixel
import utime
import uasyncio

class NeoPixelLight:
    
    presets = {
        'white': (255, 255, 255, 0),
        'full_white': (255, 255, 255, 255),
        'red': (255, 0, 0, 0),
        'green': (0, 255, 0, 0),
        'blue': (0, 0, 255, 0),
        'yellow': (255, 255, 0, 0),
        'purple': (255, 0, 255, 0),
        'sun': (255, 64, 0, 0)
        }

    def __init__(self, pin: int, num_leds: int, bpp=4):
        self.np = neopixel.NeoPixel(pin=Pin(pin), n=num_leds, bpp=bpp)
        self.led0 = 1
        self.heartbeat_on = True
        self.current_color = (0,0,0,0)
        self.brightness = 1.0 # 0 to 1 i.e. 0 to 255
        
        self.sunrise_seconds = 300 # default 5 minutes i.e. 300 seconds
        self.sunset_seconds = 300 # default 5 minutes i.e. 300 seconds
        self.light_on = False # by default at startup the light is off
        
        # make sure all pixels are off at startup
        self.change_color((0,0,0,0))


    def get_heartbeat_on(self):
        return self.heartbeat_on
    
    def toggle_heartbeat(self):
        self.heartbeat_on = False if self.heartbeat_on else True
        if self.heartbeat_on:
            self.led0 = 1
        elif not self.heartbeat_on:
            self.led0 = 0
    
    def set_brightness(self, brightness):
        r,g,b,w = self.current_color
        r = int(r * brightness)
        g = int(g * brightness)
        b = int(b * brightness)
        w = int(w * brightness)
        
        self.change_color((r,g,b,w))
    
    def toggle(self):
        '''
        Toggle light on/off
        '''
        self.off() if self.light_on else self.on()
    
    def off(self):
        '''
        Turn the light off
        '''
        print('Turning light off')
        
        color = (0,0,0,0)
        for led in range(self.led0, self.np.n):
            self.np[led] = color
        self.np.write()
        
        # reset light on flag and update current color
        self.light_on = False
        self.current_color = color   
    
    def on(self, full=True):
        '''
        Turn the light on
        '''
        print('Turning light on')
        
        color = (255,255,255,255) if full else (255,255,255,0)
        
        for led in range(self.led0, self.np.n):
            self.np[led] = color
        self.np.write()
        
        # reset light on flag and update current color
        self.light_on = True
        self.current_color = color

    def change_color(self, color: tuple):
        '''
        Change to the specified color
        '''
        for led in range(self.led0, self.np.n):
            self.np[led] = color
        self.np.write()
        
        self.current_color = color
        if self.current_color != (0,0,0,0):
            self.light_on = True

    async def fade_in(self, leds: list, color: tuple, delay: float, steps=500, start_color=(0,0,0,0)):
        '''
        Fade into a given color
        '''
        print(f'Start fade from {start_color} to {color}')
        start = utime.time()
        # get the step size for each color component
        sr, sg, sb, sw = start_color
        er, eg, eb, ew = color
        
        r_step = (er - sr) / steps
        g_step = (eg - sg) / steps
        b_step = (eb - sb) / steps
        w_step = (ew - sw) / steps
        
        for step in range(steps + 1):
            for led in leds:
                self.np[led] = (int(sr + step * r_step), int(sg + step * g_step), int(sb + step * b_step), int(sw + step * w_step))
            self.np.write()
            await uasyncio.sleep(delay/1000)
        end = utime.time()
        print(f'End fade into color {color} - elapsed time {end-start} seconds')
        self.current_color = color
    
    async def heartbeat(self, leds: list, color: tuple, delay=1, brightness=.3):
        # brightness is a number between 0 and 1
        delay = delay * 0.33 * 0.5
        r,g,b,w = color
        r = int(r * brightness)
        g = int(g * brightness)
        b = int(b * brightness)
        w = int(w * brightness)
        uasyncio.run(self.fade_in(leds=leds, start_color=(0,0,0,0), color=(r,g,b,w), delay=.3))
        uasyncio.run(self.fade_in(leds=leds, start_color=(r,g,b,w), color=(0,0,0,0), delay=.3))

    async def start_heartbeat(self, brightness=.3, delay=60):
        while self.heartbeat_on is True:
            uasyncio.create_task(self.heartbeat(leds=[0], color=NeoPixelLight.presets['red'], brightness=brightness))
            await uasyncio.sleep(delay)

    async def ambient(self, delay: float, sunset=False):
        leds = [led for led in range(self.led0, self.np.n)]
        color = (12,12,12,0) if not sunset else (0,0,0,0)
        start_color = (0,0,0,0) if not sunset else (12,12,12,0)
        uasyncio.run(self.fade_in(leds=leds, color=color, delay=delay, start_color=start_color))
    
    async def golden_hour(self, delay: float, sunset=False):
        leds = [led for led in range(self.led0, self.np.n)]
        color = (255,64,0,0) if not sunset else (12,12,12,0)
        start_color = (12,12,12,0) if not sunset else (255,64,0,0)
        uasyncio.run(self.fade_in(leds=leds, color=color, delay=delay, start_color=start_color))
    
    async def full_sun(self, delay: float, sunset=False):
        leds = [led for led in range(self.led0, self.np.n)]
        color = (255,255,255,255) if not sunset else (255,64,0,0)
        start_color = (255,64,0,0) if not sunset else (255,255,255,255)
        uasyncio.run(self.fade_in(leds=leds, color=color, delay=delay, start_color=start_color))
    
    async def sunrise(self, delay: float):#self.sunrise_seconds):
        ambient_delay = int(delay * .1)
        golden_hour_delay = int(delay * .8)
        full_sun_delay = int(delay * .2)
        await self.ambient(ambient_delay)
        await self.golden_hour(golden_hour_delay)
        await self.full_sun(full_sun_delay)
    
    async def sunset(self, delay: float):#self.sunset_seconds):
        ambient_delay = int(delay * .1)
        golden_hour_delay = int(delay * .8)
        full_sun_delay = int(delay * .2)
        await self.full_sun(full_sun_delay, sunset=True)
        await self.golden_hour(golden_hour_delay, sunset=True)
        await self.ambient(ambient_delay, sunset=True)
