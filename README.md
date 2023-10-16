# MQTT Wakeup light
A gentle way to wake up in the morning with a simulated sunrise

## Hardware
- ESP32 Wemmos Lolin 32
- Neopixel strip, 30 LEDs WS2812B RGBW
- DHT22

## How it works
- At first boot the lamp set up an AP and scans for available networks.
- The user connects to the AP and opens the wifimanager page at 192.168.4.1, select SSID and password.
- A wifi.dat file with all known network is created.
- At each new reboot the lamp scans through the known networks file and tries to connect. When connection is succeeded it creates a wifi_config.json file with the details of the network it is connected to. This is the file used by mqtt_as library to establish a reliable connection.
- Initial configurations for the alarm are set in the config.json file, which is also saved every time config features are changed by the user. The last changes are therefore reloaded at reboot.
- Time is regularly updated via worldclock API or NTP server or can be updated manually by the user via MQTT.
- When the alarm triggers, sunrise simulation starts for the amount selected by the user: i.e. if the alarm is set for 7am and the alarm delay is set for 20min, the simulation starts at 7 and completes at 7:20am.
- Recommended companion app: IoT MQTT Panel.

Brief demonstration below:

![test.gif](https://github.com/plosi/wakeuplight/blob/main/test.gif)

## Future improvements
- Add more effects (e.g. sunset, light effects, etc.)
- Add LCD screen
- Add button integration
- Connect to Home Assistant MQTT
