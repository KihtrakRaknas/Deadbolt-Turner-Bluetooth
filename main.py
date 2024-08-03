#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from bt_proximity import BluetoothRSSI
import requests_async as requests
import RPi.GPIO as gpio  # https://pypi.python.org/pypi/RPi.GPIO more info
import asyncio
import threading
import os
from flask import Flask, request
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import Device, AngularServo
Device.pin_factory = PiGPIOFactory()
app = Flask(__name__)

load_dotenv()
BT_ADDR = os.getenv('BT_ADDR')
NOTI_PROJ = os.getenv('NOTI_PROJ', "")
PASSWORD = os.getenv('PASSWORD', "")
OPEN_ANGLE = int(os.getenv('OPEN_ANGLE', "45"))
CLOSE_ANGLE = int(os.getenv('CLOSE_ANGLE', "-45"))

# Bluetooth constants
HISTORYLENGTH = int(os.getenv('TAPE_LENGTH', "200"))
CLOSELENGTH = int(os.getenv('CLOSENESS_DELAY', "4"))
CLOSETHRESH = int(os.getenv('CLOSENESS_THRESH', "3"))

# The MG90S spec sheet indicates that the min is .001 and the max is .002.
# Using .0005 and .0025 as the max and min results in the expected 180 degrees
# of motion.
door_servo = AngularServo(14, max_pulse_width=2.5/1000, min_pulse_width=.5/1000, 
                          initial_angle=None)


async def main():
    global loop
    loop = asyncio.get_event_loop()
    t1 = threading.Thread(target=server)
    t1.start()

    btrssi = BluetoothRSSI(addr=BT_ADDR)
    old_rssis = []
    
    def add_rssi(rssi_val):
        old_rssis.append(rssi_val)
        if len(old_rssis) > HISTORYLENGTH:
            old_rssis.pop(0)
    
    device_present = None
    while True:
        rssi = btrssi.request_rssi()
        print(rssi)
        if rssi is not None:
            add_rssi(rssi[0])
                
            if all(el is None for el in old_rssis):
                if device_present != False:
                    device_present = False
                    asyncio.create_task(close_door())

            if all(-CLOSETHRESH <= el <= 0 for el in old_rssis[-CLOSELENGTH:]):
                if device_present != True:
                    device_present = True
                    asyncio.create_task(open_door())
        else:
            add_rssi(None)
            
        await asyncio.sleep(1)


async def open_door():
    print("open door called")
    asyncio.create_task(notif_call("opened door"))
    door_servo.angle = OPEN_ANGLE
    await asyncio.sleep(3)
    door_servo.detach()
    
    
async def close_door():
    print("close door called")
    asyncio.create_task(notif_call("closed door"))
    door_servo.angle = CLOSE_ANGLE
    await asyncio.sleep(3)
    door_servo.detach()


def valid_password(request):
    valid = False
    if PASSWORD == "":
        valid = True
    if request.method == "GET" and request.args['password'] == PASSWORD:
        valid = True
    if request.method == "POST":
        if request.json["password"] == PASSWORD:
            valid = True
    return valid

def server():
    @app.route('/open', methods=['GET', 'POST'])
    def respond():
        print("open called")
        if valid_password(request):
            asyncio.run_coroutine_threadsafe(open_door(), loop)
            return 'Done'
        return 'Invalid Password'
    
    
    @app.route('/close', methods=['GET', 'POST'])
    def respond():
        print("close called")
        if valid_password(request):
            asyncio.run_coroutine_threadsafe(close_door(), loop)
            return 'Done'
        return 'Invalid Password'


    @app.route('/reboot', methods=['GET', 'POST'])
    def reboot():
        if valid_password(request):
            os.system('sudo shutdown -r now')
            return 'Done'
        return "Invalid Password"
    from waitress import serve
    
    serve(app, host="0.0.0.0", port=8080)
    # app.run()


async def notif_call(str):
    if NOTI_PROJ != '':
        await requests.get(f"https://n.kihtrak.com/?project={NOTI_PROJ}&title={str}")


if __name__ == '__main__':
    asyncio.run(main())