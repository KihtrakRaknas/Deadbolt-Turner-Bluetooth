# Door Handle Automator

## Demo Video
You can see a demo here: [https://youtu.be/ZAB0t-3RGFY?si=TFmU06qy9ATIXA8a](https://youtu.be/ZAB0t-3RGFY?si=TFmU06qy9ATIXA8a)

## Set Up
This code was written to run on a raspberry pi. I have tested both a raspberry pi 4 and a raspberry pi zero. The set up instructions for both devices are the same.
### Install Requirements
1. Get the bluetooth package:
   ```sh
   sudo apt-get install --no-install-recommends bluetooth
   ```
2. Install an additional module:
   ```sh
   sudo apt-get install python3-bluez
   ```
3. Install python modules:
   ```sh
   pip install -r requirements.txt
   ```
### Grab Bluetooth Address
4. Get the phone you want to detect's bluetooth address by setting your phone to discoverable and then running:
   ```sh
   hcitool scan
   ```
5. Available devices should be listed. Copy the address of your device.
### Set up the program to run on start up
6. Edit your rc.local file:
   ```sh
   sudo nano /etc/rc.local
   ```
7. Add code to run the script at start up:
   ```sh
   sudo python /home/pi/Documents/DoorOpenerProject/main.py -b <bluetoothaddress> &
   ```
   - `<bluetoothaddress>` is the bluetooth address from step 5.
   You can add optional arguements:
   - `-n <notibotproject>` is a project name from https://notibot.kihtrak.com
   - `-p <password>` is a password to call the webhook with
8. Reboot the pi and it should start working

## Usage
Door handle should open automatically when it detects your phone coming up to the door.


Call the webhook at `<ip/localhost>:8080/webhook` and in the post request send the json: `{password:<your password>}`. (Only need to include password if you set one with the optional arguement).

## Related Repos:
- [dingdong](https://github.com/KihtrakRaknas/dingdong) - A website that acts like a virtual door bell for the door
- [dingdongserver](https://github.com/KihtrakRaknas/dingdongserver) - The backend for the ding dong website
