import utime
from machine import Pin, Signal, unique_id, reset, ADC
import ubinascii
from umqtt.simple import MQTTClient
from NetworkConnect import get_server_ip, safe_connect_to_network
# import logging            # logging doesn't seem to work by default??


import senko

OTA = senko.Senko(None, None,
                  url="https://raw.githubusercontent.com/Aaron-Wrote-This/plug_controller/master",
                  files=["boot.py", "main.py"]
                  )

# mosquitto_pub -t ACCommands -m "on"
SERVER = get_server_ip()                            # Server IP address
CLIENT_ID = ubinascii.hexlify(unique_id())          # ID of client to be used by MQTT Server

MQTT_TOPIC = b'OUTDOOR_PLUG'     # Topic specifc for this device
MQTT_COMMAND = b''


def process_pushbutton(button_pin, relay_pin, prev_button_state, prev_time, debounce_time):
    button_state = button_pin.value()   # only read the button once
    # print(button_state)
    # check if the button is being pressed and check that this button press has not already been dealt with, and
    # check if the button just bounced up and down
    if button_state and not prev_button_state and utime.ticks_diff(utime.ticks_ms(), prev_time) > debounce_time:
        relay_pin.value(not relay_pin.value())  # set the relay
        print('Turning on relay because of button press')
        prev_time = utime.ticks_ms()             # record when the button was last pressed for debouncing
    prev_button_state = button_state    # record the button state to see if we've processed this one yet
    return prev_button_state, prev_time


def toggle_relay_from_message(relay_1, relay_2):
    global MQTT_COMMAND
    if MQTT_COMMAND != b'':
        relay, command = str(MQTT_COMMAND).split(':')
        if relay == "relay_1":
            relay = relay_1
        elif relay == "relay_2":
            relay = relay_2
        else:
            print("Error reading relay: '{}'".format(MQTT_COMMAND))

        if command == '1' and not relay.value():
            relay.on()
        elif command == '0' and relay.value():
            relay.off()
        else:
            print("no toggle needed, was already set correctly")

    MQTT_COMMAND = b''


class RelayWithStatusLED(Pin):
    def __init__(self, relay_pin_number: int, led_pin_number: int):
        """Class to manage both the relays and LEDs
        On this outdoor plug the leds are inverted..."""
        super().__init__(relay_pin_number, Pin.OUT)
        self.led = Signal(Pin(led_pin_number, Pin.OUT), invert=True)

    def on(self):
        super().on()
        self.led.on()

    def off(self):
        super().off()
        self.led.off()

    def value(self, new_val=None):
        # Passing None turns it off? So I guess I need to pass literally nothing
        if new_val is not None:
            self.led.value(new_val)
            return super().value(new_val)
        else:
            self.led.value()
            return super().value()


def receive_message(topic, msg):
    # print("{} : {}".format(topic, msg))
    if topic == MQTT_TOPIC:
        # print("Correct topic")
        global MQTT_COMMAND
        if MQTT_COMMAND == b'':
            MQTT_COMMAND = msg


def main():
    try:
        print("Booting main")

        # define standard vars

        button_1 = Pin(18, Pin.IN, Pin.PULL_DOWN)
        button_2 = Pin(17, Pin.IN, Pin.PULL_DOWN)

        status_led = Signal(Pin(5, Pin.OUT), invert=True)

        # relay_1 = Pin(15, Pin.OUT)
        relay_1 = RelayWithStatusLED(15, 19)

        relay_2 = RelayWithStatusLED(32, 16)

        lux_sensor = ADC(34)        # .5 < low; high > .5

        # todo maybe implement, doesn't seem to be a library tho
        power_sel = Pin(25, Pin.OUT)
        power_cf = Pin(27, Pin.IN)
        power_cf1 = Pin(26, Pin.IN)

        prev_button_state_1 = 0  # previous state of the button
        prev_button_state_2 = 0  # previous state of the button

        status_led.on()        # status led, just showing alive right now
        # todo flash led when wifi connects and flash it if wifi isn't connected?
        # ex flash_led_patterns.append([1,2])
        # flashes the led twice with 1 second gaps inbetween
        # flash_led_patterns = []

        # setup customizable vars
        debounce_time = 200  # the debounce time, increase if the output flickers
        prev_time_1 = 0
        prev_time_2 = 0

        prev_ota_update_check = utime.time()

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
                    c.subscribe(MQTT_TOPIC)
                    mqtt_connected = True

                    print("mqtt connection worked!")
                except:
                    print("connecting failed, still trying")
            if not mqtt_connected and mqtt_connection_time + 500 > utime.time():
                reset()

            if mqtt_connected and wifi_connected:
                status_led.off()
            else:
                status_led.on()

            # if prev_ota_update_check + 300 < utime.time():
            #     prev_ota_update_check = utime.time()
            #     print("Checking OTA Update!")
            #     if OTA.update():
            #         print("YES OTA updating!")
            #         reset()
            #     else:
            #         print("No OTA Update")

            prev_button_state_1, prev_time_1 = process_pushbutton(button_1, relay_1, prev_button_state_1, prev_time_1,
                                                                  debounce_time)
            prev_button_state_2, prev_time_2 = process_pushbutton(button_2, relay_2, prev_button_state_2, prev_time_2,
                                                                  debounce_time)

            if mqtt_connected:
                c.check_msg()
                toggle_relay_from_message(relay_1, relay_2)

            utime.sleep_ms(100)

    except Exception as e:
        print("Something went wrong, trying to reboot?\nHere was the error {}".format(e))
        utime.sleep(3)
        reset()


# if __name__ == "__main__":
#     main()
main()
