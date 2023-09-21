from wifi import connect, disconnect
import utime
import mqtt
from umqtt.robust import MQTTClient
from light import WakeUpLight

disconnect
utime.sleep_ms(250)
connected = connect()

client_id = 'wakeuplight'
broker = 'io.adafruit.com'
port = 1883
username = 'pl0s1'
password = 'ee1f01b973f1c2ceb9c14b5f1d9be342e5484410'

STRIP_PIN = 16
NUM_LEDS = 30

mqtt_client = MQTTClient(client_id, broker, port, username, password, 60)
topic_prefix = f'{username}/feeds'

if connected:
    l = WakeUpLight(STRIP_PIN, NUM_LEDS, mqtt_client, topic_prefix)
    while True:
        l.client.wait_msg()

# if connected:
#     l = 

# if connected:
#     print('Successfully connected')
#     c = mqtt.mqtt_connect()
#     #mqtt.mqtt_pub(topic='pl0s1/feeds/sunrise', msg='start')
#     while True:
#         c.wait_msg()
    