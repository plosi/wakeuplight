import gc
gc.enable()
gc.collect()

from microdot_asyncio import Microdot, send_file

from machine import Pin
import utime
import uasyncio
import dht

dht_config = {
    'dht_pin': 13,
    'dht_vcc': 12,
    'dht_gnd': 14
    }

btn_config = {
    'btn_pin': 0
    }

class NeoPixelWebServer:
    
    current_task = None
    
    def __init__(self, neopixel_obj, neopixel_alarm_obj, dht_config: dict, btn_config: dict):
        self.app = Microdot()
        self.neo = neopixel_obj
        self.neo_alarm = neopixel_alarm_obj
        
        self.dht_init()
        self.btn_init()
    
    def dht_init(self):
        print('Initializing DHT sensor...')
        
        gnd = Pin(dht_config['dht_gnd'], Pin.OUT)
        vcc = Pin(dht_config['dht_vcc'], Pin.OUT)
        self.dht = dht.DHT22(Pin(dht_config['dht_pin']))
        
        gnd.off()
        vcc.on()
    
    def btn_init(self):
        print('Initializing BTN...')
        
        self.btn = Pin(btn_config['btn_pin'], Pin.IN, Pin.PULL_UP)
    
    @self.app.before_request
    async def pre_request_handler(self, request):
        if NeoPixelConnect.current_task:
            NeoPixelConnect.current_task.cancel()

    @self.app.route('/')
    async def index(self, request):
        return send_file('/static/index.html')

    @self.app.route('/bootstrap.min.css')
    async def css(self, request):
        return send_file('/static/bootstrap.min.css')

    @self.app.route('/bootstrap.bundle.min.js')
    async def js(self, request):
        return send_file('/static/bootstrap.bundle.min.js')

    @self.app.route('/jquery-3.3.1.min.js')
    async def jquery(self, request):
        return send_file('/static/jquery-3.3.1.min.js')

    @self.app.route('/jscolor.js')
    async def js_color(self, request):
        return send_file('/static/jscolor.js')
    
    # Start webserver
    async def start_server(self):
        while True:
            print('Starting microdot app')
            try:
                self.app.run(port=80)
            except:
                self.app.shutdown()
            await uasyncio.sleep(0)
    
    @self.app.post('/api')
    async def handle_request(self, request):
        try:
            api = request.json
            action = api.action
            if action == 'toggle_light':
                self.neo.toggle()
            
            elif action == 'set_brightness':
                brightness = float(api.brightness)
                self.neo.set_brightness(brightness)
            
            elif action == 'toggle_heartbeat':
                self.neo.heartbeat_on = False if self.neo.heartbeat_on else True
            
            elif action == 'set_rgbw':
                color = api.color
                self.neo.change_color(color)
            
            elif action == 'set_utc_offset':
                self.neo_alarm.utc_offset = int(api.utc_offset) * 3600
            
            elif action == 'set_dst_offset':
                self.neo_alarm.dst_offset = int(api.dst_offset) * 3600
            
            elif action == 'set_alarm_hour':
                self.neo.alarm_hour = int(api.alarm_hour)
            
            elif action == 'set_alarm_minute':
                self.neo.alarm_minute = int(api.alarm_minute)
            
            elif action == 'set_alarm_delay':
                self.neo.alarm_delay = int(api.alarm_delay)
            
            elif action == 'toggle_alarm':
                self.neo.alarm_on = False if self.neo.alarm_on else True
            
            elif action == 'get_alarm_settings':
                response_obj = {
                    'alarm_on': self.neo.alarm_on,
                    'alarm_time': f'{self.neo.alarm_hour}:{self.neo.alarm_minute}',
                    'alarm_delay': self.neo.alarm_delay
                    }
                return response_obj
            
            elif action == 'get_localtime':
                dt = utime.localtime()
                response_obj = {
                    'date': f'{dt[2]:02d}/{dt[1]:02d}/{dt[0]}',
                    'localtime': f'{dt[3]:02d}:{dt[4]:02d}:{dt[5]:02d}',
                    'utc_time': f'{utime.gmtime()[3]:02d}:{utime.gmtime()[4]:02d}:{utime.gmtime()[5]:02d}',
                    'utc_offset': f'{utc_offset}',
                    'dst_offset': f'{dst_offset}'
                    }
                return response_obj
            
            elif action == 'get_dht':
                self.dht.measure()
                temp = self.dht.temperaure()
                rhum = self.dht.humidity()
                response_obj = {
                    'temp': temp,
                    'rhum': rhum
                    }
                return response_obj
        
        except OSError as e:
            print(f'Connection error {e.errno}: {e}')
