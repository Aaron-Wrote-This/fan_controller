from time import sleep, time
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


def toggle_ac(on_off):  # Takes on/off input
    if on_off == 'on':  # sanity check to see if input is valid, otherwise return error
        direction = 1
    elif on_off == 'off':
        direction = -1
    else:
        return '-1'
    print("toggle command working : {}".format(on_off))
    list_of_pins = [14, 12, 13, 15]  # pins being used to control motor
    initialized_list_of_pins = []
    list_of_states = [[1, 1, 0, 0], [0, 1, 1, 0], [0, 0, 1, 1], [1, 0, 0, 1]]  # states to full step
    one_revolution = 2048  # number of steps in a full revolution of my motor (28BYJ-48 12v)
    # rotation_amt = int((one_revolution / 4) / 4)         # good for lightswitch
    rotation_amt = int((one_revolution / 4) / 2 + (one_revolution / 4 / 3) - 20)            # rotation amt for AC

    speed = 0.005 # 0.005  # 0.002 		# 0.002 is fastest   # speed I've found most effective for strengh/speed to flip my AC

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
        sleep(5)
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
                sleep(3)

        print("connection worked!")

        global AC_COMMAND, KEEP_ALIVE
        # previous_time = time()
        while True:
            c.wait_msg()
            if AC_COMMAND == b'1':
                print("ac turn on")
                toggle_ac("on")
                AC_COMMAND = b''
            elif AC_COMMAND == b'0':
                print("ac turn off")
                toggle_ac("off")
                AC_COMMAND = b''
            else:
                print("Ac command = {}".format(AC_COMMAND))
            # if KEEP_ALIVE == b'1':
            #     previous_time = time()
            #     KEEP_ALIVE = b''
            # if (time() - previous_time) > 30:
            #     print("I'm dead")
            #     reset()
    except Exception as e:
        print("Something went wrong, trying to reboot?\nHere was the error {}".format(e))
        sleep(3)


# if __name__ == "__main__":
#     main()
main()
