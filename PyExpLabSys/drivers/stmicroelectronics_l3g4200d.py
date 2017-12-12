""" Driver for STMicroelectronics L3G4200D 3 axis gyroscope """
import os
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'
if on_rtd:
    pass
else:
    import smbus
import time
from PyExpLabSys.common.supported_versions import python2_and_3
python2_and_3(__file__)

class L3G4200D(object):
    """ Class for reading accelerometer output """

    def __init__(self):
        self.bus = smbus.SMBus(1)
        self.device_address = 0x68
        # Set output data rate to 200, bandwidth cut-off to 12.5Hz
        self.bus.write_byte_data(self.device_address, 0x20, 0x4F)
        # Set full scale range, 0x00: 250dps, 0x30: 2000dps
        self.full_scale = 250 # This should go in a self-consistent table...
        self.bus.write_byte_data(self.device_address, 0x23, 0x00)
        time.sleep(0.5)

    def who_am_i(self):
        """ Device identification """
        id_byte = self.bus.read_byte_data(self.device_address, 0x0F)
        return id_byte
        
    

    def read_values(self):
        """ Read a value from the sensor """
        new_data = self.bus.read_byte_data(self.device_address, 0x27)
        print(bin(new_data))

        byte1 = self.bus.read_byte_data(self.device_address, 0x28)
        byte2 = self.bus.read_byte_data(self.device_address, 0x29)

        x_value = byte2 * 256 + byte1
        if x_value > 32767:
            x_value = x_value - 65536
        x_value = 1.0 * x_value * self.full_scale / 65536

        byte1 = self.bus.read_byte_data(self.device_address, 0x2A)
        byte2 = self.bus.read_byte_data(self.device_address, 0x2B)
        y_value = byte2 * 256 + byte1
        if y_value > 32767:
            y_value = y_value - 65536
        y_value = 1.0 * y_value * self.full_scale / 65536

        byte1 = self.bus.read_byte_data(self.device_address, 0x2C)
        byte2 = self.bus.read_byte_data(self.device_address, 0x2D)
        z_value = byte2 * 256 + byte1
        if z_value > 32767:
            z_value = z_value - 65536
        z_value = 1.0 * z_value * self.full_scale / 65536

        
        return(x_value, y_value, z_value)

if __name__ == '__main__':
    AIS = AIS328DQTR()
    #print(bin(AIS.who_am_i()))
    for i in range(0, 5):
        time.sleep(0.01)
        print(AIS.read_values())