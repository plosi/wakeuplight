from machine import Pin, SoftI2C
import neopixel
import utime
import uasyncio

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

class NeoPixelLight:
    
    sunrise_seconds = 300 # default 5 minutes i.e. 300 seconds
    light_on = False # by default at startup the light is off
    
    def __init__(self, pin: int, num_leds: int, bpp=4):
        self.np = neopixel.NeoPixel(pin=Pin(pin), n=num_leds, bpp=bpp)        
        
        # make sure all pixels are off
        self.change_color((0,0,0,0))
    
    def off(self):
        '''
        Turn the light off
        '''
        print('Turning light off')
        
        color = (0,0,0,0)
        for led in range(self.np.n):
            self.np[led] = color
        self.np.write()
        
        # reset light on flag
        light_on = False
    
    
    def on(self, full=True):
        '''
        Turn the light on
        '''
        print('Turning light on')
        
        color = (255,255,255,255) if full else (255,255,255,0)
        
        for led in range(self.np.n):
            self.np[led] = color
        self.np.write()
        
        # reset light on flag
        light_on = True


    def change_color(self, color: tuple):
        '''
        Change to the specified color
        '''
        for led in range(self.np.n):
            self.np[led] = color
        self.np.write()


    async def fade_in(self, leds: list, color: tuple, delay: int, steps=500, start_color=(0,0,0,0)):
        '''
        Fade into a given color
        '''
        print(f'Start fade into color {color}')
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
    
    async def ambient(self, delay: int):
        leds = [led for led in range(self.np.n)]
        color = (12,12,12,0)
        uasyncio.run(self.fade_in(leds=leds, color=color, delay=delay))
    
    async def golden_hour(self, delay: int):
        leds = [led for led in range(self.np.n)]
        color = (255,64,0,0)
        uasyncio.run(self.fade_in(leds=leds, color=color, delay=delay, start_color=(12,12,12,0)))
    
    async def full_sun(self, delay: int):
        leds = [led for led in range(self.np.n)]
        color = (255,255,255,255)
        uasyncio.run(self.fade_in(leds=leds, color=color, delay=delay, start_color=(255,64,0,0)))
    
    async def sunrise(self, delay=sunrise_seconds):
        ambient_delay = int(delay * .1)
        golden_hour_delay = int(delay * .8)
        full_sun_delay = int(delay * .2)
        await self.ambient(ambient_delay)
        await self.golden_hour(golden_hour_delay)
        await self.full_sun(full_sun_delay)


### TESTING
# neo = NeoPixelLight(STRIP_PIN, NUM_LEDS)
# 
# # coroutines main
# async def main():
# #     uasyncio.create_task(neo.fade_in(leds=[12,13,14], color=red, delay=15))
# #     uasyncio.create_task(neo.fade_in(leds=[7,9,11], color=blue, delay=5))
#     await neo.sunrise(60)
#     await uasyncio.sleep(0)
#     
# #    while True:
# #        await neo.full_sun()
# #         await uasyncio.sleep(0)
#     
# try:
#     uasyncio.run(main())
# finally:
#     uasyncio.new_event_loop()
