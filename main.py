from microdot_asyncio import Microdot
from wifi import do_connect
from machine import Pin, SoftI2C, WDT, RTC
import utime
import uasyncio
import ntptime
import urequests
import dht
import ssd1306

from light import NeoPixelLight

STRIP_PIN = 16
NUM_LEDS = 30

DHT_PIN = 13
DHT_GND = 14
DHT_VCC = 12

SDA_PIN = 5
SCL_PIN = 4

# Global variables
current_task = None
utc_offset = 3600 # in seconds
dst_offset = 0 # also in seconds
alarm_on = True
alarm_hour = 6
alarm_minute = 5
sunrise_duration = 20 * 60 # seconds
alarm_run = False

# dht
# display

##################
### Web Server ###
##################

# Setup web server
app = Microdot()

@app.before_request
async def pre_request_handler(request):
    if current_task:
        current_task.cancel()

@app.route('/')
async def hello(request):
    return 'Hello world'

@app.route('/setRGBW')
async def setRGBW(request):
    # http://<IP addr>/setRGBW?r=255&g=64&b=0&w=0
    color = (int(request.args['r']), int(request.args['g']), int(request.args['b']), int(request.args['w']))
    neo.change_color(color)
    return 'OK'

@app.route('/on')
async def switch_on(request):
    # http://<IP addr>/on
    neo.on()
    return 'OK'

@app.route('/off')
async def switch_off(request):
    # http://<IP addr>/off
    neo.off()
    return 'OK'

@app.route('/sunrise')
async def sunrise(request):
    # http://<IP addr>/sunrise
    global current_task
    current_task = uasyncio.create_task(neo.sunrise())
    return 'OK'

@app.route('/get_localtime')
async def get_localtime(request):
    # http://<IP addr>/get_localtime
    dt = utime.localtime()#utime.gmtime(utime.time() + utc_offset + dst_offset)
    dt_dict = {'date': f'{dt[2]:02d}/{dt[1]:02d}/{dt[0]}',
               'localtime': f'{dt[3]:02d}:{dt[4]:02d}:{dt[5]:02d}',
               'utc_time': f'{utime.gmtime()[3]:02d}:{utime.gmtime()[4]:02d}:{utime.gmtime()[5]:02d}',
               'utc_offset': f'{utc_offset}',
               'dst_offset': f'{dst_offset}'}
    return dt_dict

@app.route('/dht')
async def get_dht(request):
    # http://<IP addr>/dht
    dht.measure()
    dht_dict = {'temp': dht.temperature(), 'rhum': dht.humidity()}
    return dht_dict

@app.route('/set_alarm_time')
async def set_alarm_time(request):
    # http://<IP addr>/set_alarm_time?hr=6&mn=5&duration_min=20
    global sunrise_duration
    alm_hr = int(request.args['hr'])
    alm_mn = int(request.args['mn'])
    sunrise_duration = int(request.args['duration_min']) * 60
    init_alarm(alm_hr, alm_mn)
    return f'Alarm set for {alm_hr:02d}:{alm_mn:02d}, with a duration of {int(sunrise_duration/60)} minutes'

@app.route('/toggle_alarm')
async def toggle_alarm(request):
    # http://<IP addr>/toggle_alarm?on=1
    al_on = True if int(request.args['on']) == 1 else False
    init_alarm(al_on=al_on)
    return f'Alarm set to {al_on}'


# Start webserver
async def start_server():
    while True:
        print('Starting microdot app')
        try:
            app.run(port=80)
        except:
            app.shutdown()
        await uasyncio.sleep(0)



#######################
### Time and Alarms ###
#######################

def update_time():
    global utc_offset
    global dst_offset
    
    try:
        response = urequests.get('http://worldtimeapi.org/api/ip')
        if response.status_code == 200:
            print('API time updated')
            parsed = response.json()
            utc_offset = parsed['raw_offset']
            dst_offset = parsed['dst_offset']
            dt = utime.localtime(parsed['unixtime'] + utc_offset + dst_offset - 946684800)
            RTC().datetime((dt[0], dt[1], dt[2], dt[6] + 1, dt[3], dt[4], dt[5], 0))
    except:
        try:
            ntptime.settime()
            dt = utime.localtime(utime.mktime(utime.localtime()) + utc_offset + dst_offset)
            RTC().datetime((dt[0], dt[1], dt[2], dt[6] + 1, dt[3], dt[4], dt[5], 0))
            print('NTP time updated')
        except:
            print('Impossible to update time: no connection?')
            dt = utime.gmtime(utime.time() + utc_offset + dst_offset)
            RTC().datetime((dt[0], dt[1], dt[2], dt[6] + 1, dt[3], dt[4], dt[5], 0))
    print(f'{dt[2]:02d}/{dt[1]:02d}/{dt[0]} {dt[3]:02d}:{dt[4]:02d}:{dt[5]:02d}')


async def get_time(delay):
    while True:
        dt = utime.localtime()#utime.localtime(utime.mktime(utime.localtime()) + utc_offset + dst_offset)
        date_str = f'{dt[2]:02d}/{dt[1]:02d}/{dt[0]}'
        time_str = f'{dt[3]:02d}:{dt[4]:02d}:{dt[5]:02d}'
#         print(f'{date_str} {time_str}')
        display.fill(0)
        display.text(time_str, 0, 0, 1)
        display.show()
        await uasyncio.sleep(delay)

async def regularly_update_time(delay):
    while True:
        update_time()
        await uasyncio.sleep(delay)

        
def init_alarm(hour=alarm_hour, minute=alarm_minute, al_on=alarm_on):
    global alarm_hour
    global alarm_minute
    global alarm_on
    
    alarm_hour = hour
    alarm_minute = minute
    alarm_on = al_on
    

async def check_for_alarm(delay):
    global alarm_run
    global current_task
    
    while True:
        now_hr = utime.localtime()[3]
        now_mn = utime.localtime()[4]
        
        if alarm_on:
            if (now_hr == alarm_hour) & (now_mn == alarm_minute) & (alarm_run is not True):
                alarm_run = True
                current_task = uasyncio.create_task(neo.sunrise(delay=sunrise_duration))
            # reset the alarm_run flag once the alarm is terminated
            elif alarm_run:
                if (now_hr >= alarm_hour) & (now_mn > int(alarm_minute + sunrise_duration / 60)):
                    alarm_run = False
        
        await uasyncio.sleep(delay)

###########
### DHT ###
###########

def dht_init():
    print('Initializing DHT sensor...')
    global dht
    
    gnd = Pin(DHT_GND, Pin.OUT)
    vcc = Pin(DHT_VCC, Pin.OUT)
    dht = dht.DHT22(Pin(DHT_PIN))
    
    gnd.off()
    vcc.on()

async def get_dht(delay):
    while True:
        try:
            dht.measure()
            temp_str = f'Temp: {dht.temperature()} °C'
            rhum_str = f'RHum: {dht.humidity()} %'
            print(f'{temp_str}\n{rhum_str}')
        except:
            print('dht error')
        await uasyncio.sleep(delay)


###############
### Display ###
###############

def oled_init():
    print('Initializing OLED display...')
    global display
    i2c = SoftI2C(sda=Pin(SDA_PIN), scl=Pin(SCL_PIN))
    display = ssd1306.SSD1306_I2C(128, 64, i2c)


######################
### Task Scheduler ###
######################

# tasks/coroutines
async def coroutines():
    uasyncio.create_task(start_server())
    uasyncio.create_task(regularly_update_time(300))
    uasyncio.create_task(check_for_alarm(0.2))
    uasyncio.create_task(get_time(1))
    uasyncio.create_task(get_dht(120))
    
    while True:
        await uasyncio.sleep(0)

if __name__ == '__main__':
    neo = NeoPixelLight(STRIP_PIN, NUM_LEDS)
    #do_connect()
    if do_connect() is not False:
        initial_msg = 'Connected'
    else:
        initial_msg = 'Offline'
#     wdt = WDT(timeout=60 * 1000)  # enable it with a timeout of 60s
    oled_init()
    
    display.fill(0)
    display.text(f'{initial_msg}', 0, 0, 1)
    display.show()
    
    dht_init()
    
    utime.sleep(3)
#     wdt.feed()

    uasyncio.run(coroutines())
        
