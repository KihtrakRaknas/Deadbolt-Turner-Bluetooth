import binascii
import time
from bluepy.btle import Scanner, BTLEInternalError, ScanEntry

class ScannerWStop(Scanner):
    def __init__(self, iface=0):
        Scanner.__init__(self, iface)
        self.terminate_process = False
        
    def process(self, timeout=30.0): # Changed default timeout
        if self._helper is None:
            raise BTLEInternalError(
                                "Helper not started (did you call start()?)")
        start = time.time()
        while True:
            if timeout:
                remain = start + timeout - time.time()
                if remain <= 0.0 or self.terminate_process == True: # self.terminate_process is new
                    self.terminate_process = False # new
                    break
            else:
                remain = None
            resp = self._waitResp(['scan', 'stat'], remain)
            if resp is None:
                break

            respType = resp['rsp'][0]
            if respType == 'stat':
                # if scan ended, restart it
                if resp['state'][0] == 'disc':
                    self._mgmtCmd(self._cmd())

            elif respType == 'scan':
                # device found
                addr = binascii.b2a_hex(resp['addr'][0]).decode('utf-8')
                addr = ':'.join([addr[i:i+2] for i in range(0,12,2)])
                if addr in self.scanned:
                    dev = self.scanned[addr]
                else:
                    dev = ScanEntry(addr, self.iface)
                    self.scanned[addr] = dev
                isNewData = dev._update(resp)
                if self.delegate is not None:
                    self.delegate.handleDiscovery(dev, (dev.updateCount <= 1), isNewData)
                 
            else:
                raise BTLEInternalError("Unexpected response: " + respType, resp)