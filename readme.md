# Door Handle Automator

## Set Up
This code was written to run on a raspberry pi. I have tested both a raspberry pi 4 and a raspberry pi zero. The set up instructions for both devices are the same.
1. Get the bluetooth package:
   ```sh
   sudo apt-get install --no-install-recommends bluetooth
   ```

2. Get the phone you want to detect's bluetooth address by setting your phone to discoverable and then running:
   ```sh
   hcitool scan
   ```
3. Available devices should be listed. Copy the address of your device.
4. Install an additional module:
   ```sh
   sudo apt-get install python3-bluez
   ```
5. Install python modules:
   ```sh
   pip install -r requirements.txt
   ```
6. Edit your rc.local file:
   ```sh
   sudo nano /etc/rc.local
   ```
7. Add code to run the script at start up:
   ```sh
   sudo python /home/pi/Documents/DoorOpenerProject/main.py -b <bluetoothadress> &
   ```
8. Reboot the pi and it should start working