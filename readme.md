# Door Opener (Pi Zero)

## Parts

This project is meant to turn the deadbolt in my apartment. I 3D modeled the
parts used to make the whole thing work. They can be viewed here:
[https://a360.co/3W8fSmm](https://a360.co/3W8fSmm)

## Set Up

This code was written to run on a raspberry pi. I have tested both a raspberry pi 4 and a raspberry pi zero. The set up instructions for both devices are the same.

### Install Requirements

1. Get the required packages:

   ```sh
   sudo apt-get install git python3-pip libglib2.0-dev python3-pigpio python3-bluez
   sudo apt-get install --no-install-recommends bluetooth
   pip install pipenv --user --break-system-packages
   python3 -m pipenv install
   ```

2. Make sure bluetooth isn't blocked:

   ```sh
   sudo rfkill unblock bluetooth
   ```

3. Get the python path for later:

   ```sh
   python3 -m pipenv run which python
   ```

4. Enable PiGPIO on startup:

   ```sh
   sudo pigpiod
   sudo systemctl enable pigpiod
   ```

### Grab Bluetooth Address

5. Get the phone you want to detect's bluetooth address by setting your phone to discoverable and then running:

   ```sh
   hcitool scan
   ```

6. You may need to pair the devices. You can do this with the `bluetoothctl` utility:
   ```sh
   bluetoothctl
   ```
   Then run the following commands:
   ```
   agent on
   scan on
   discoverable on
   pair <device address>
   ```

### Set Up Environment variables

7. Make a copy of `.env.template` named `.env`.

8. Use the value copied earlier for the BT_ADDR variable. Optionally, set up the
other variables.

9. Available devices should be listed. Copy the address of your device.

### Set up the program to run on start up

10. Create a service to start the python script on startup:

   ```sh
   sudo nano /etc/systemd/system/door.service
   ```

   Example file:

   ```
   [Unit]
   Description=Start door script
   After=network.target
   After=bluetooth.target

   [Service]
   User=root
   ExecStart=[python path from step 2] [path to main.py]
   WorkingDirectory=/home/pi/Deadbolt-Turner-Bluetooth
   StandardOutput=inherit
   StandardError=inherit
   Restart=always
   Environment="PYTHONUNBUFFERED=1"

   [Install]
   WantedBy=multi-user.target
   ```

   Then enable the service

   ```sh
   sudo systemctl daemon-reload
   sudo systemctl enable door.service
   ```

11. Reboot the pi and it should start working

## Usage

Door handle should open automatically when it detects your phone coming up to the door.
And close when it detect your phone leaving.


Call the webhook at `<ip/localhost>:8080/open` or `<ip/localhost>:8080/close` and in the post request send the json: `{password:<your password>}`. (Only need to include password if you set one with the optional argument).

## Related Repos:
- [dingdong](https://github.com/KihtrakRaknas/dingdong) - A website that acts like a virtual door bell for the door
- [dingdongserver](https://github.com/KihtrakRaknas/dingdongserver) - The backend for the ding dong website
