#!/usr/bin/env python3
from bt_proximity import BluetoothRSSI
import time
import sys, getopt
import requests_async as requests
import RPi.GPIO as gpio  # https://pypi.python.org/pypi/RPi.GPIO more info
import atexit
import asyncio
import threading
import datetime
from flask import Flask, request
app = Flask(__name__)


# iphone 13 pro: 'F8:C3:CC:9C:C9:6C'


motor_lock = asyncio.Lock()

notibot_project = ''
password = ''
guestpassword = ''

async def main():
    BT_ADDR = ''
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hb:n:p:", ["bluetoothaddress=", "notibotproject=", "password="])
    except getopt.GetoptError:
        print('USAGE: main.py -b <bluetoothaddress> [-n <notibotproject>] [-p <password>]')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('USAGE: main.py -b <bluetoothaddress> [-n <notibotproject>] [-p <password>]')
            sys.exit()
        elif opt in ("-b", "--bluetoothaddress"):
            BT_ADDR = arg
        elif opt in ("-n", "--notibotproject"):
            global notibot_project
            notibot_project = arg
        elif opt in ("-p", "--password"):
            global password
            password = arg
        elif opt in ("-g", "--guestpassword"):
            global guestpassword
            guestpassword = arg
    if BT_ADDR == '':
        print('USAGE: main.py -b <bluetoothaddress>')
        sys.exit()

    global loop
    loop = asyncio.get_event_loop()
    set_up_motor()
    t1 = threading.Thread(target=server)
    t1.start()
    # asyncio.create_task(open_door())
    # await asyncio.sleep(1000)
    btrssi = BluetoothRSSI(addr=BT_ADDR)
    old_rssi = None
    old_rssis = []
    while True:
        rssi = btrssi.request_rssi()
        print(rssi)
        if rssi is None:
            if not (old_rssi is None):
                old_rssi = None
                old_rssis = [-50]*100
                # loop = asyncio.get_event_loop()
                asyncio.create_task(notif_call("phone%20lost"))
        else:
            rssi = rssi[0]

            old_rssis.append(rssi)
            if len(old_rssis) > 100:
                old_rssis.pop(0)

            if old_rssi is None:
                old_rssi = rssi
                asyncio.create_task(notif_call("phone%20detected"))
            else:
                print(str(all(-20 <= el <= 0 for el in (old_rssis[-5:]))) + " & " + str(not any(-20 <= el <= 0 for el in (old_rssis[:80]))))
                if all(-20 <= el <= 0 for el in (old_rssis[-5:])) and not any(-20 <= el <= 0 for el in (old_rssis[:80])):
                    asyncio.create_task(open_door())
        await asyncio.sleep(.01)


async def open_door():
    print("open door called")
    if motor_lock.locked():
        return
    async with motor_lock:
        asyncio.create_task(notif_call("open%20door"))
        gpio.output(25, True) # Stop the motor from sleeping
        gpio.output(23, False) # Set the direction

        StepCounter = 0
        WaitTime = 0.0005
        Steps = 4800
        while StepCounter < Steps:
            # turning the gpio on and off tells the easy driver to take one step
            gpio.output(24, True)
            gpio.output(24, False)
            StepCounter += 1

            # Wait before taking the next step...this controls rotation speed
            time.sleep(WaitTime)
            #await asyncio.sleep(WaitTime)

        await asyncio.sleep(15)
        
        StepCounter = 0
        gpio.output(23, True) # Reverse direction
        while StepCounter < Steps:
            # turning the gpio on and off tells the easy driver to take one step
            gpio.output(24, True)
            gpio.output(24, False)
            StepCounter += 1

            # Wait before taking the next step...this controls rotation speed
            time.sleep(WaitTime)
            #await asyncio.sleep(WaitTime)

        gpio.output(25, False)  # Motor goes back to sleeping
        asyncio.create_task(notif_call("close%20door"))


def server():
    @app.route('/webhook', methods=['GET', 'POST'])
    def respond():
        print("webhook called");
        valid = False
        if password == "":
            valid = True
        if request.json["password"] == password:
            valid = True
        if request.json["password"] == guestpassword:
            now = datetime.datetime.now()
            # Monday is 0
            if (1 == now.weekday() or 3 == now.weekday()) and datetime.time(hour=8, minute=30) <= now.time() <= datetime.time(hour=9, minute=30):
                valid = True
            requests.get('https://n.kihtrak.com/?project='+notibot_project+'&title=Guest%20Door%20Open%20Request&body=Valid:%20'+str(valid))
        if valid:
            asyncio.run_coroutine_threadsafe(open_door(), loop)
            return 'Done'
        return 'Invalid Password';
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)
    # app.run()


async def notif_call(str):
    if notibot_project != '':
        await requests.get('https://n.kihtrak.com/?project='+notibot_project+'&title='+str)


def set_up_motor():
    # use the broadcom layout for the gpio
    gpio.setmode(gpio.BCM)
    # GPIO23 = Direction
    # GPIO24 = Step
    # GPIO25 = SLEEP
    gpio.setup(23, gpio.OUT)
    gpio.setup(24, gpio.OUT)
    gpio.setup(25, gpio.OUT)

    gpio.output(25, False) # Make the motor sleep


def exit_handler():
    gpio.cleanup()


atexit.register(exit_handler)

if __name__ == '__main__':
    asyncio.run(main())

