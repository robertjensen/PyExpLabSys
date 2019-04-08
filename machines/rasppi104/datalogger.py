""" Pressure and temperature logger """
import threading
import time
import logging
from PyExpLabSys.common.database_saver import ContinuousDataSaver
#from PyExpLabSys.common.sockets import LiveSocket
from PyExpLabSys.common.sockets import DateDataPullSocket
from PyExpLabSys.common.value_logger import ValueLogger
import PyExpLabSys.drivers.honeywell_6000 as honeywell_6000
import wiringpi as wp # pylint: disable=F0401
import credentials

class MovementReader(threading.Thread):
    """ Movement reader """
    def __init__(self):
        threading.Thread.__init__(self)
        wp.wiringPiSetup()
        self.movement = 0
        self.quit = False
        self.ttl = 20

    def value(self):
        """ Read movement """
        self.ttl = self.ttl - 1
        if self.ttl < 0:
            self.quit = True
            return_val = None
        else:
            return_val = self.movement
        return return_val

    def run(self):
        movement = 0
        for _ in range(0, 10):
            movement = movement + wp.digitalRead(4)
            time.sleep(0.1)
        self.movement = float(movement) / 10
        while not self.quit:
            self.ttl = 200
            movement = 0
            avg_length = 100
            for _ in range(0, avg_length):
                movement = movement + wp.digitalRead(4)
                time.sleep(0.25)
            self.movement = float(movement) / avg_length


class Reader(threading.Thread):
    """ Pressure reader """
    def __init__(self, honeywell):
        threading.Thread.__init__(self)
        self.honeywell = honeywell
        self.temperature = None
        self.humidity = None
        self.quit = False
        self.ttl = 20

    def value(self, channel):
        """ Read temperature and  pressure """
        self.ttl = self.ttl - 1
        if self.ttl < 0:
            self.quit = True
            return_val = None
        else:
            if channel == 1:
                return_val = self.temperature
            if channel == 2:
                return_val = self.humidity
        return return_val

    def run(self):
        while not self.quit:
            time.sleep(2)
            self.ttl = 50
            avg_length = 50
            humidity = 0
            temperature = 0
            for _ in range(0, avg_length):
                time.sleep(0.1)
                hum, temp = self.honeywell.read_values()
                humidity += hum
                temperature += temp
            self.temperature = temperature / avg_length
            self.humidity = humidity / avg_length

def main():
    """ Main function """
    logging.basicConfig(filename="logger.txt", level=logging.ERROR)
    logging.basicConfig(level=logging.ERROR)

    hih_instance = honeywell_6000.HIH6130()
    reader = Reader(hih_instance)
    reader.start()

    movement_reader = MovementReader()
    movement_reader.start()

    time.sleep(15)

    codenames = ['home_temperature_living_room', 'home_humidity_living_room',
                 'home_movement_living_room']

    loggers = {}
    loggers[codenames[0]] = ValueLogger(reader, comp_val=0.2, comp_type='lin',
                                        channel=1)
    loggers[codenames[0]].start()
    loggers[codenames[1]] = ValueLogger(reader, comp_val=0.25, comp_type='lin',
                                        channel=2)
    loggers[codenames[1]].start()
    loggers[codenames[2]] = ValueLogger(movement_reader, comp_val=0.1,
                                        comp_type='lin')
    loggers[codenames[2]].start()

    #livesocket = LiveSocket('Home Air Logger', codenames)
    #livesocket.start()

    #socket = DateDataPullSocket('Home Air Logger', codenames,
    #                            timeouts=[1.0] * len(loggers))
    #socket.start()

    table = 'dateplots_rued_langgaards_vej'
    db_logger = ContinuousDataSaver(continuous_data_table=table,
                                    username=credentials.user,
                                    password=credentials.passwd,
                                    measurement_codenames=codenames)
    db_logger.start()

    while reader.isAlive():
        time.sleep(1)
        for name in codenames:
            value = loggers[name].read_value()
            #livesocket.set_point_now(name, value)
            # socket.set_point_now(name, value)
            if loggers[name].read_trigged():
                print(value)
                db_logger.save_point_now(name, value)
                loggers[name].clear_trigged()

if __name__ == '__main__':
    main()
