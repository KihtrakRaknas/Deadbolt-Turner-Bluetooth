import time
from scanner_patch import ScannerWStop
from bluepy.btle import DefaultDelegate, BTLEDisconnectError
        
class MyDelegate(DefaultDelegate):
    def __init__(self, target_address, scanner):
        DefaultDelegate.__init__(self)
        self.target_address = target_address
        self.scanner = scanner
        self.device_rssi = None

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if dev.addr.lower() == self.target_address.lower():
            self.device_rssi = dev.rssi
            self.scanner.terminate_process = True

def get_device_rssi(target_address, timeout=30):
    scanner = ScannerWStop()
    delegate = MyDelegate(target_address, scanner)
    scanner.withDelegate(delegate)

    scanner.start()
    scanner.process(timeout=timeout)
    scanner.stop()
    return delegate.device_rssi

# Source: https://iot.stackexchange.com/a/3330
# This was measured by putting a iPhone 15 pro 1 meter away from the pi zero w 2
def rssi_to_distance(rssi, calibrated_rssi=-50):
    return 10 ** ((calibrated_rssi - rssi) / (10 * 2))

def get_distance_to_device(target_address, timeout=30):
    max_retries = 2
    for attempt in range(max_retries):
        try:
            rssi = get_device_rssi(target_address, timeout=timeout)
            break
        except BTLEDisconnectError:
            if attempt == max_retries - 1:
                raise
            time.sleep(5)
            continue
    if rssi is not None:
        return rssi_to_distance(rssi)
    return None