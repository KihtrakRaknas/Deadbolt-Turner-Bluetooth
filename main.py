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
import os
from flask import Flask, request
app = Flask(__name__)

# Stepper motor constants
STEPTIME = 0.0002
STEPS = 1960
PRIMESTEPS = 1500
SLEEPPIN = 25
STEPPIN = 24
DIRPIN = 23
CLOCKWISE = True
RESETTIME = .4
HOLDTIME = 20

# Bluetooth constants
HISTORYLENGTH = 200
CLOSELENGTH = 4
CLOSETHRESH = 3
FARLENGTH = 40
FARTHRESH = 12

# iphone 13 pro: 'F8:C3:CC:9C:C9:6C'

motor_lock = asyncio.Lock()

notibot_project = ''
password = ''
guestpassword = ''

async def main():
    BT_ADDR = ''
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hb:n:p:g:", ["bluetoothaddress=", "notibotproject=", "password=","guestpassword="])
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
    delete_me = False
    while True:
        rssi = btrssi.request_rssi()
        print(rssi)
        if rssi is None:
            old_rssis = [-100]*HISTORYLENGTH
            if not (old_rssi is None):
                old_rssi = None
                # asyncio.create_task(notif_call("phone%20lost"))
                delete_me = False
        else:
            rssi = rssi[0]

            old_rssis.append(rssi)
            if len(old_rssis) > HISTORYLENGTH:
                old_rssis.pop(0)

            if old_rssi is None:
                old_rssi = rssi
                # asyncio.create_task(notif_call("phone%20detected"))
            else:
                print(str(old_rssis[:FARLENGTH]))
                print(str(all(-CLOSETHRESH <= el <= 0 for el in (old_rssis[-CLOSELENGTH:]))) + " & " + str(not any(-FARTHRESH <= el <= 0 for el in (old_rssis[:FARLENGTH]))))
                if any(-FARTHRESH <= el <= 0 for el in (old_rssis[:FARLENGTH])) and not delete_me:
                    delete_me = True
                    # asyncio.create_task(notif_call("Too late: "+str(old_rssis)))

                if all(-CLOSETHRESH <= el <= 0 for el in (old_rssis[-CLOSELENGTH:])) and not any(-FARTHRESH <= el <= 0 for el in (old_rssis[:FARLENGTH])):
                    old_rssis = [0]*HISTORYLENGTH
                    asyncio.create_task(open_door())
        await asyncio.sleep(1)


async def open_door():
    print("open door called")
    if motor_lock.locked():
        return
    async with motor_lock:
        def init():
            gpio.output(SLEEPPIN, True) # Stop the motor from sleeping
            gpio.output(DIRPIN, CLOCKWISE) # Set the direction
            
        def step(steps):
            stepCounter = 0
            while stepCounter < steps:
                # Tell the easy driver to take one step
                gpio.output(STEPPIN, True)
                gpio.output(STEPPIN, False)
                stepCounter += 1
    
                # Wait before taking the next step...this controls rotation speed
                time.sleep(STEPTIME)

        async def sleep():
            gpio.output(25, False)  # Motor goes back to sleeping
            await asyncio.sleep(RESETTIME)
            
        asyncio.create_task(notif_call("opened%20door"))
        
        init()
        step(PRIMESTEPS)
        await sleep()
        # init()
        # step(PRIMESTEPS)
        # await sleep()
        init()
        step(STEPS)
        await asyncio.sleep(HOLDTIME)
        await sleep()
        
        # asyncio.create_task(notif_call("close%20door"))


def server():
    @app.route('/webhook', methods=['GET', 'POST'])
    def respond():
        print("webhook called")
        valid = False
        if password == "":
            valid = True
        if request.method == "GET" and request.args['password'] == password:
            valid = True
        if request.method == "POST":
            if request.json["password"] == password:
                valid = True
            if guestpassword!= "" and request.json["password"] == guestpassword:
                now = datetime.datetime.now()
                # Monday is 0
                if (1 == now.weekday() or 3 == now.weekday()) and datetime.time(hour=8, minute=30) <= now.time() <= datetime.time(hour=9, minute=30):
                    valid = True
                notif_call('Guest%20Door%20Open%20Request')#&body=Valid%3A%20'+str(valid))
                if not valid:
                    return "Guest password not allowed at this time"
        if valid:
            asyncio.run_coroutine_threadsafe(open_door(), loop)
            return 'Done'
        return 'Invalid Password'

    @app.route('/reboot', methods=['GET', 'POST'])
    def reboot():
        if request.json["password"] != password:
            return "Invalid Password"
        os.system('sudo shutdown -r now')
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

