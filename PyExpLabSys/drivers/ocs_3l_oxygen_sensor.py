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
    def __init__(self, port='/dev/serial1', humidity_sensor=False):
        self.ser = serial.Serial(port, 9600, timeout=2)
        self.humidity_sensor = humidity_sensor
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

    def _read_flow(self, data):
        flow = (data[5] * 256 + data[6]) / 10.0
        return flow

    def _read_humidity(self, data):
        if self.humidity_sensor:
            humidity = data[7]
        else:
            humidity = -1
        return humidity

    def _read_temperature(self, data):
        if self.humidity_sensor:
            temperature = data[8]
        else:
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
        # This function is deprecated. Use read_all_values()
        data = self.read()

        checksum = self._check_full_checksum(data)
        if not checksum:
            return None

        concentration = self._read_oxygen(data)
        temperature = self._read_temperature(data)
        # msg = 'Oxygen concentration: {}%, Temperature: {}C. Checksum: {}'
        # print(msg.format(concentration, temperature, checksum))
        return (concentration, temperature)

    def read_all_values(self):
        data = self.read()

        checksum = self._check_full_checksum(data)
        if not checksum:
            return None

        concentration = self._read_oxygen(data)
        temperature = self._read_temperature(data)
        humidity = self._read_humidity(data)
        flow = self._read_flow(data)
        return (concentration, temperature, humidity, flow)


if __name__ == '__main__':
    wp.wiringPiSetup()
    wp.digitalWrite(6, 1)
    wp.digitalWrite(7, 0)

    oxygen_sensor = OCS3L(port='/dev/serial1', humidity_sensor=True)
    while True:
        readout = oxygen_sensor.read_all_values()
        if readout is not None:
            print('O2: {}%. Temp {}C. Hum: {}%. Flow: {}L/min'.format(*readout))
        else:
            print('Missed read')
