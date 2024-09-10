# Door Opener (Pi Zero)

## Parts

This project is meant to turn the deadbolt in my apartment. I 3D modeled the
parts used to make the whole thing work. They can be viewed here:
[https://a360.co/3W8fSmm](https://a360.co/3W8fSmm)

## Set Up

This code was written to run on a raspberry pi. I have tested both a raspberry pi 4 and a raspberry pi zero. The set up instructions for both devices are the same.

### Install Requirements

1. Get the bluetooth package:

   ```sh
   sudo apt-get install --no-install-recommends bluetooth
   ```

2. Install additional modules:

   ```sh
   sudo apt-get install python3-bluez
   sudo apt-get install python3-pigpio
   ```

3. Install python modules:

   ```sh
   # install pipenv
   pip install pipenv --user --break-system-packages
   curl https://pyenv.run | bash

   python3 -m pipenv install --deploy
   ```

4. Enable PiGPIO on startup:

   ```sh
   sudo systemctl enable pigpiod
   ```

### Grab Bluetooth Address

5. Get the phone you want to detect's bluetooth address by setting your phone to discoverable and then running:

   ```sh
   hcitool scan
   ```

### Set Up Environment variables

6. Make a copy of `.env.template` named `.env`.

7. Use the value copied earlier for the BT_ADDR variable. Optionally, set up the
other variables.

8. Available devices should be listed. Copy the address of your device.

### Set up the program to run on start up

9. Edit your rc.local file:

   ```sh
   sudo nano /etc/rc.local
   ```

10. Add code to run the script at start up:

   ```sh
   pipenv run python ~/Documents/Deadbolt-Turner-Bluetooth/main.py &
   ```

11. Reboot the pi and it should start working

## Usage

Door handle should open automatically when it detects your phone coming up to the door.
And close when it detect your phone leaving.


Call the webhook at `<ip/localhost>:8080/open` or `<ip/localhost>:8080/close` and in the post request send the json: `{password:<your password>}`. (Only need to include password if you set one with the optional argument).

## Related Repos:
- [dingdong](https://github.com/KihtrakRaknas/dingdong) - A website that acts like a virtual door bell for the door
- [dingdongserver](https://github.com/KihtrakRaknas/dingdongserver) - The backend for the ding dong website
