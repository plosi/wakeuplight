
### TESTING light
# neo = NeoPixelLight(STRIP_PIN, NUM_LEDS)
#
# async def main():
#     while True:
#         await neo.heartbeat(leds=[0], color=(255,0,0,0), delay=0.25, brightness=.3)
#         await uasyncio.sleep(0)
# 
# uasyncio.run(main())
# 
# # coroutines main
# async def main():
# #     uasyncio.create_task(neo.fade_in(leds=[12,13,14], color=red, delay=15))
# #     uasyncio.create_task(neo.fade_in(leds=[7,9,11], color=blue, delay=5))
#     await neo.sunrise(60)
#     await uasyncio.sleep(0)
#     
#         while True:
#            await neo.full_sun()
#            await uasyncio.sleep(0)
#     
# try:
#     uasyncio.run(main())
# finally:
#     uasyncio.new_event_loop()
