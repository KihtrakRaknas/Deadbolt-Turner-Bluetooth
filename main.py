#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from proximity import get_distance_to_device
import requests
import asyncio
import threading
from flask import Flask, request
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import Device, AngularServo
from waitress import serve
from functools import wraps
Device.pin_factory = PiGPIOFactory()
app = Flask(__name__)

load_dotenv()
BT_ADDR = os.getenv('BT_ADDR')
NOTI_PROJ = os.getenv('NOTI_PROJ', "")
PASSWORD = os.getenv('PASSWORD', "")
OPEN_ANGLE = int(os.getenv('OPEN_ANGLE', "45"))
CLOSE_ANGLE = int(os.getenv('CLOSE_ANGLE', "-45"))
PORT = int(os.getenv('PORT', "8080"))

# Bluetooth constants
HISTORYLENGTH = int(os.getenv('TAPE_LENGTH', "200"))
CLOSELENGTH = int(os.getenv('CLOSENESS_DELAY', "4"))
CLOSETHRESH = float(os.getenv('CLOSENESS_THRESH', "3"))
DOOROPENDURATION = int(os.getenv('DOOROPENDURATION', "60"))

# The MG90S spec sheet indicates that the min is .001 and the max is .002.
# Using .0005 and .0025 as the max and min results in the expected 180 degrees
# of motion.
door_servo = AngularServo(12, max_pulse_width=2.5/1000, min_pulse_width=.5/1000, 
                          initial_angle=None)


async def main():
    global loop
    loop = asyncio.get_event_loop()
    t1 = threading.Thread(target=server)
    t1.start()
    t2 = threading.Thread(target=monitor_bluetooth)
    t2.start()
    while True:
        await asyncio.sleep(1)

def monitor_bluetooth():
    old_distances = []

    def add_to_tape(val):
        old_distances.append(val)
        if len(old_distances) > HISTORYLENGTH:
            old_distances.pop(0)

    device_present = None
    while True:
        distance = get_distance_to_device(BT_ADDR, timeout=45)
        print(distance)
        add_to_tape(distance)
        if all(el is not None and el <= CLOSETHRESH for el in old_distances[-CLOSELENGTH:]):
            if device_present == False:
                device_present = True
                asyncio.run_coroutine_threadsafe(open_and_close_door(), loop)
        elif distance is None:
            if device_present != False:
                device_present = False
                asyncio.run_coroutine_threadsafe(close_door(), loop)

        asyncio.run_coroutine_threadsafe(asyncio.sleep(1), loop)


async def open_and_close_door():
    if DOOROPENDURATION == -1:
        await open_door()
        return
    print("open and close door called")
    asyncio.create_task(notif_call(f"Opened door for {DOOROPENDURATION} seconds"))
    door_servo.angle = OPEN_ANGLE
    await asyncio.sleep(3)
    door_servo.detach()
    await asyncio.sleep(DOOROPENDURATION)
    door_servo.angle = CLOSE_ANGLE
    await asyncio.sleep(3)
    door_servo.detach()


async def open_door():
    print("open door called")
    asyncio.create_task(notif_call("Opened door"))
    door_servo.angle = OPEN_ANGLE
    await asyncio.sleep(3)
    door_servo.detach()
    
    
async def close_door():
    print("close door called")
    asyncio.create_task(notif_call("Closed door"))
    door_servo.angle = CLOSE_ANGLE
    await asyncio.sleep(3)
    door_servo.detach()


def server():
    def valid_password(func):
        @wraps(func)
        def valid_password_wrapper(*args, **kwargs):
            if PASSWORD == "":
                return func(*args, **kwargs)
            if request.method == "GET" and request.args['password'] == PASSWORD:
                return func(*args, **kwargs)
            if request.method == "POST":
                if request.json["password"] == PASSWORD:
                    return func(*args, **kwargs)
            return 'Invalid Password'
        
        return valid_password_wrapper
    

    @app.route('/open', methods=['GET', 'POST'])
    @valid_password
    def respond_open():
        print("open called")
        asyncio.run_coroutine_threadsafe(open_door(), loop)
        print("return done")
        return 'Done'
    
    
    @app.route('/close', methods=['GET', 'POST'])
    @valid_password
    def respond_close():
        print("close called")
        asyncio.run_coroutine_threadsafe(close_door(), loop)
        return 'Done'


    @app.route('/reboot', methods=['GET', 'POST'])
    @valid_password
    def reboot():
        os.system('sudo shutdown -r now')
        return 'Done'
    
    asyncio.run_coroutine_threadsafe(notif_call(f"Starting server on port {PORT}"), loop)
    serve(app, host="0.0.0.0", port=PORT)


async def notif_call(str):
    if NOTI_PROJ != '':
        requests.get(f"https://n.kihtrak.com/?project={NOTI_PROJ}&title={str}")


if __name__ == '__main__':
    asyncio.run(main())
