import utime
from machine import Pin, unique_id
import ubinascii
from umqtt.simple import MQTTClient
from NetworkConnect import get_server_ip
# import logging            # logging doesn't seem to work by default??

# mosquitto_pub -t ACCommands -m "on"
SERVER = get_server_ip()                            # Server IP address
CLIENT_ID = ubinascii.hexlify(unique_id())          # ID of client to be used by MQTT Server
TOPIC_KEEPALIVE = b"keepAlive"                   # bedroomEnvironment, "livingroomEnvironment", "basementEnvironment"
TOPIC_AC = b'ACCommands'                            # Topic for on/off command
AC_COMMAND = b''
KEEP_ALIVE = b'0'



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

    try:
        for pin in list_of_pins:  # setup all pins as outputs and set them to off position
            initialized_list_of_pins.append(Pin(pin, Pin.OUT))           # annoyingly Pin (cap) is a function
            print("Set pin " + str(pin) + " to out")

        for pin in range(0, 4):
            initialized_list_of_pins[pin](0)

        list_of_state_positions = range(0, 4)  # indexing pin states so it can be reversed easily
        for x in range(rotation_amt):  # inside /4 is because the "pin in range" does 4 steps at once,
            for state in list_of_state_positions[::direction]:  # the outer is to make one quarter of a revolution in total
                for pin in range(0, 4):
                    initialized_list_of_pins[pin](list_of_states[state][pin])  # setting pin {list of pins} to state {list of states}
                sleep(speed)
        # in thhis version motor doesn''t return I think
        # for x in range(int((one_revolution / 4) / 4)):  # reversing motor back to original location
        #     for state in list_of_state_positions[::int((-1) * direction)]:
        #         for pin in range(0, 4):
        #             initialized_list_of_pins[pin](list_of_states[state][pin])
        #         sleep(speed)
    finally:
        for pin in range(0, 4):
            initialized_list_of_pins[pin](0)
            print("Set pin " + str(pin) + " to off")
    return '1'  # ideally would somehow make blocking, idk how to do that, might auto happen?


def receive_message(topic, msg):
    # print("{} : {}".format(topic, msg))
    if topic == TOPIC_AC:
        # print("Correct topic")
        global AC_COMMAND
        if AC_COMMAND == b'':
            # print("AC topic is null(good)")
            if msg == b'on':
                # print("msg was on good!\n\n\n")
                AC_COMMAND = b'0'
            elif msg == b'off':
                AC_COMMAND = b'1'
    elif topic == TOPIC_KEEPALIVE:
        global KEEP_ALIVE
        KEEP_ALIVE = b'1'


def connect_c(c):                                        # connect call, works mostly
    c.connect()
    c.set_callback(receive_message)
    c.subscribe(TOPIC_AC)
    c.subscribe(TOPIC_KEEPALIVE)


def ping():
    ...


def pong():
    ...


def main():
    try:
        print("Booting main")
        print("Sleeping 5 seconds")
        utime.sleep(5)
        c = MQTTClient(CLIENT_ID, SERVER)

        connected = False
        while not connected:
            print("attempting connection")
            try:
                connect_c(c)
                connected = True
            except:
                print("connecting failed, still trying")
                connected = False
                utime.sleep(3)

        print("connection worked!")

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

        # setup customizable vars
        debounce_time = 200  # the debounce time, increase if the output flickers
        prev_time = 0

        # main loop
        while True:
            prev_button_state, prev_time = process_pushbutton(button_pin, relay_pin, prev_button_state, prev_time, debounce_time)
            c.check_msg()
            toggle_relay_from_message(relay_pin)
            utime.sleep_ms(100)

    except Exception as e:
        print("Something went wrong, trying to reboot?\nHere was the error {}".format(e))
        utime.sleep(3)


# if __name__ == "__main__":
#     main()
main()
