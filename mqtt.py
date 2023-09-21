import network
from utime import sleep, sleep_ms
import json
from umqtt.robust import MQTTClient

client_id = 'wakeuplight'
broker = 'io.adafruit.com'
port = 1883
username = 'pl0s1'
password = 'ee1f01b973f1c2ceb9c14b5f1d9be342e5484410'

sub_topic_prefix = f'{username}/feeds'
sub_topic_general = f'{sub_topic_prefix}/#'

topics = ['sunrise', 'sunset', 'toggle', 'color']

def mqtt_cb(topic, msg):
    full_topic = topic.decode('utf-8')
    msg = msg.decode('utf-8')
    print(f'topic: {full_topic} -- message: {msg}')
    
    topic = full_topic.split('/')[-1]
#     print(topic)
    
    if topic == f'sunrise':
        if msg == 'start':
            # start sunrise
            print('start sunrise')
        elif msg == 'stop':
            # stop sunrise and switch off
            print('stop sunrise')
    elif topic == 'sunset':
        if msg == 'start':
            # start sunset
            print('start sunset')
        elif msg == 'stop':
            # stop sunset and switch off
            print('stop sunset')
    elif topic == 'toggle':
        if msg == '1':
            print('Toggle 1')
        elif msg == '0':
            print('Toggle 0')
    elif topic == 'color':
        print('Change color')
    

def mqtt_connect():
    global client
    reconnect = True
    client = MQTTClient(client_id, broker, port, username, password, 60)
    client.set_callback(mqtt_cb)
    
    while reconnect:
        try:
            client.connect()
            reconnect = False
        except:
            print(f'Connecting to {broker}...')
            sleep(10)
            
    print(f'Connected to {broker}')
    for topic in topics:
        client.subscribe(f'{sub_topic_prefix}/{topic}')
#     mqtt_update_light()
    return client

def mqtt_sub():
    return

def mqtt_pub(topic, msg):
    client.publish(topic, msg, True)