# This file is executed on every boot (including wake-boot from deepsleep)
# import esp
# esp.osdebug(None)


# import webrepl
# webrepl.start()

import gc
gc.collect()

import NetworkConnect
NetworkConnect.connect_to_network()

# import time
# import machine
# blueled = machine.Pin(2, machine.Pin.OUT)

# for i in range(3):
#     blueled.off()
#     time.sleep(0.5)
#     blueled.on()
#     time.sleep(0.5)

print("DONE!")
