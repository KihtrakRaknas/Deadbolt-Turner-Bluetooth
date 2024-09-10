import bluetooth
import bluetooth._bluetooth as bt
import struct
import re
from bt_proximity import BluetoothRSSI

class BluetoothRSSIPatched(BluetoothRSSI):
    def request_rssi_int(self):
        if rssi := self.request_rssi():
            return rssi[0]
        return rssi
    
    
    def request_rssi(self):
        try:
            # If socket is closed, return nothing
            if self.closed:
                return None
            # Only do connection if not already connected
            if not self.connected:
                self.connect()
            # Command packet prepared each iteration to allow disconnect to trigger IOError
            self.prep_cmd_pkt()
            # Send command to request RSSI
            try:
                rssi = bt.hci_send_req(
                    self.hci_sock, bt.OGF_STATUS_PARAM,
                    bt.OCF_READ_RSSI, bt.EVT_CMD_COMPLETE, 4, self.cmd_pkt)
            except UnicodeDecodeError as err:
                match = re.search(r"\s(0x[0-9a-fA-F]+)\s", str(err))
                if match:
                    byte_val = int(match.group(1), 16)
                    return struct.unpack('b', byte_val.to_bytes(1, 'big'))
                else:
                    raise err
            rssi = bytes(rssi, 'latin1')
            rssi = struct.unpack('b', rssi[3].to_bytes(1, 'big'))
            return rssi
        except IOError:
            # Happens if connection fails (e.g. device is not in range)
            self.connected = False
            # Socket recreated to allow device to successfully reconnect
            self.bt_sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
            return None 