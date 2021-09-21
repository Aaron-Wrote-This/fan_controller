# This file is executed on every boot (including wake-boot from deepsleep)
# import esp
# esp.osdebug(None)
import gc
import NetworkConnect
# import webrepl
# webrepl.start()
gc.collect()

NetworkConnect.connect_to_network()
