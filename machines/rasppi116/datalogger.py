""" Pressure and temperature logger """
import threading
import time
import logging
from PyExpLabSys.common.database_saver import ContinuousDataSaver
#from PyExpLabSys.common.sockets import LiveSocket
from PyExpLabSys.common.sockets import DateDataPullSocket
from PyExpLabSys.common.value_logger import ValueLogger
import PyExpLabSys.drivers.honeywell_6000 as honeywell_6000
import credentials

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

    print('wait start 15s')
    time.sleep(15)
    print('Wait end')
    codenames = ['home_temperature_bathroom', 'home_humidity_bathroom']

    loggers = {}
    loggers[codenames[0]] = ValueLogger(reader, comp_val=0.2, comp_type='lin',
                                        channel=1)
    loggers[codenames[0]].start()
    loggers[codenames[1]] = ValueLogger(reader, comp_val=0.25, comp_type='lin',
                                        channel=2)
    loggers[codenames[1]].start()

    #livesocket = LiveSocket('Home Air Logger', codenames)
    #livesocket.start()

    socket = DateDataPullSocket('Home Air Logger', codenames,
                                timeouts=[1.0] * len(loggers))
    socket.start()

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
            socket.set_point_now(name, value)
            if loggers[name].read_trigged():
                print(value)
                db_logger.save_point_now(name, value)
                loggers[name].clear_trigged()

if __name__ == '__main__':
    main()
