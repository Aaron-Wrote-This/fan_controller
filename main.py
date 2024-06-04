import utime
from machine import Pin, unique_id, reset
import ubinascii
from umqtt.simple import MQTTClient
from NetworkConnect import get_server_ip, safe_connect_to_network
# import logging            # logging doesn't seem to work by default??


# import senko
#
# OTA = senko.Senko( None, None,
#     url="https://raw.githubusercontent.com/Aaron-Wrote-This/fan_controller/master",
#     files=["boot.py", "main.py"]
# )


# mosquitto_pub -t ACCommands -m "on"
SERVER = get_server_ip()                            # Server IP address
CLIENT_ID = ubinascii.hexlify(unique_id())          # ID of client to be used by MQTT Server
# TOPIC_KEEPALIVE = b"keepAlive"                   # bedroomEnvironment, "livingroomEnvironment", "basementEnvironment"
# KEEP_ALIVE = b'0'

TOPIC_FAN_PLUG = b'PrinterPlug'                            # Topic for on/off command
FAN_COMMAND = b''


def process_pushbutton(button_pin, relay_pin, prev_button_state, prev_time, debounce_time):
    button_state = not button_pin.value()   # only read the button once
    # print(button_state)
    # check if the button is being pressed and check that this button press has not already been dealt with, and
    # check if the button just bounced up and down
    if button_state and not prev_button_state and utime.ticks_diff(utime.ticks_ms(), prev_time) > debounce_time:
        relay_pin.value(not relay_pin.value())  # set the relay
        print('Turning on relay because of button press')
        prev_time = utime.ticks_ms()             # record when the button was last pressed for debouncing
    prev_button_state = button_state    # record the button state to see if we've processed this one yet
    return prev_button_state, prev_time


def toggle_relay_from_message(relay_pin: Pin):
    global FAN_COMMAND
    if FAN_COMMAND != b'':
        print('toggleing relay because of mqtt command')
        if FAN_COMMAND == b'1' and relay_pin.value() != 1:
            relay_pin.on()
        elif FAN_COMMAND == b'0' and relay_pin.value() != 0:
            relay_pin.off()
        else:
            print("no toggle needed, was already set correctly")
    FAN_COMMAND = b''


def receive_message(topic, msg):
    # print("{} : {}".format(topic, msg))
    if topic == TOPIC_FAN_PLUG:
        # print("Correct topic")
        global FAN_COMMAND
        if FAN_COMMAND == b'':
            # print("AC topic is null(good)")
            if msg == b'ON':
                # print("msg was on good!\n\n\n")
                FAN_COMMAND = b'1'
            elif msg == b'OFF':
                FAN_COMMAND = b'0'
    # elif topic == TOPIC_KEEPALIVE:
    #     global KEEP_ALIVE
    #     KEEP_ALIVE = b'1'


def main():
    print("Version 1")
    # Connect to wifi
    #   if that fails wait 5 mins and try to reconnect
    # Connect to mqtt, if that fails wait 5 mins and try to reconnect

    try:
        print("Booting main")

        # define standard vars
        button_pin_number = 0  # Sonoff On/Off button
        relay_pin_number = 12  # Sonoff relay
        led_pin_number = 13  # Sonoff green LED - always on

        prev_button_state = 0  # previous state of the button

        # init pins
        button_pin = Pin(button_pin_number, Pin.IN, Pin.PULL_UP)
        relay_pin = Pin(relay_pin_number, Pin.OUT)
        led_pin = Pin(led_pin_number, Pin.OUT)

        led_pin.on()        # status led, just showing alive right now
        # todo flash led when wifi connects and flash it if wifi isn't connected?
        # ex flash_led_patterns.append([1,2])
        # flashes the led twice with 1 second gaps inbetween
        # flash_led_patterns = []

        # setup customizable vars
        debounce_time = 200  # the debounce time, increase if the output flickers
        prev_time = 0

        # prev_ota_update_check = utime.time()

        wifi_connected = False
        mqtt_connected = False

        # main loop
        while True:
            wifi_connection_time = utime.time()
            # todo check if wifi really is connected, instead of just running this the first time
            if not wifi_connected:
                wifi_connected = safe_connect_to_network()
                wifi_connection_time = utime.time()
                print("wifi connection worked!")
                utime.sleep(5)
            if not wifi_connected and wifi_connection_time + 500 > utime.time():
                reset()

            mqtt_connection_time = utime.time()
            # todo check if mqtt really is connected, instead of just running this the first time
            if not mqtt_connected:
                try:
                    c = MQTTClient(CLIENT_ID, SERVER)
                    c.connect()
                    c.set_callback(receive_message)
                    c.subscribe(TOPIC_FAN_PLUG)
                    mqtt_connected = True

                    print("mqtt connection worked!")
                except:
                    print("connecting failed, still trying")
            if not mqtt_connected and mqtt_connection_time + 500 > utime.time():
                reset()

            # if prev_ota_update_check + 300 > utime.time():
            #     if OTA.update():
            #         reset()


            prev_button_state, prev_time = process_pushbutton(button_pin, relay_pin, prev_button_state, prev_time, debounce_time)

            if mqtt_connected:
                c.check_msg()
                toggle_relay_from_message(relay_pin)

            utime.sleep_ms(100)

    except Exception as e:
        print("Something went wrong, trying to reboot?\nHere was the error {}".format(e))
        utime.sleep(3)
        reset()


# if __name__ == "__main__":
#     main()
main()
