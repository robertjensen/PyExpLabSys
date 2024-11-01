"""
Bit-banged driver for oxygen sensor. Can also work with
a proper 3.3V uart.

Notice that this sensor is highly cross-sensitive to other
gasses than oxygen.
"""
import time

import serial
import wiringpi as wp


class OCS3L(object):
    def __init__(self, port='/dev/serial1'):
        self.ser = serial.Serial(port, 9600, timeout=2)
        time.sleep(0.1)

    def read(self):
        _ = self.ser.read(self.ser.inWaiting())
        start = b''
        while not (start == b'\x16\t\x01'):
            start = self.ser.read(3)
        rest = self.ser.read(9)
        data = start + rest
        return data

    def _read_oxygen(self, data):
        concentration = (data[3] * 256 + data[4]) / 10.0
        return concentration

    def _read_temperature(self, data):
        temperature = (data[7] * 256 + data[8]) / 10.0
        return temperature

    def _check_full_checksum(self, data):
        expected_checksum = 0
        for val in data[:-1]:
            expected_checksum += val
            expected_checksum = expected_checksum % 256
        expected_checksum = 256 - expected_checksum

        success = (expected_checksum == data[-1])
        return success

    def read_oxygen_and_temperature(self):
        data = self.read()

        checksum = self._check_full_checksum(data)
        if not checksum:
            return None

        concentration = self._read_oxygen(data)
        temperature = self._read_temperature(data)
        # msg = 'Oxygen concentration: {}%, Temperature: {}C. Checksum: {}'
        # print(msg.format(concentration, temperature, checksum))
        return(concentration, temperature)


if __name__ == '__main__':
    oxygen_sensor = OCS3L(port='/dev/serial1')
    while True:
        readout = oxygen_sensor.read_oxygen_and_temperature()
        if readout is not None:
            print('Oxygen: {}%. Temperature: {}C'.format(readout[0], readout[1]))
        else:
            print('Missed read')
