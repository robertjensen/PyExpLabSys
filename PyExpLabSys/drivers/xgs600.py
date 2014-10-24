import serial
import time


class XGS600Driver():
    def __init__(self, port='/dev/ttyUSB1'):
        self.f = serial.Serial(port)

    def xgs_comm(self, command):
        """ Implements basic communication """
        self.f.read(self.f.inWaiting()) # Clear waiting characters
        comm = "#00" + command + "\r"
        self.f.write(comm)
        time.sleep(0.25)
        number_of_bytes = self.f.inWaiting()
        complete_string = self.f.read(number_of_bytes)
        complete_string = complete_string.replace('>', '').replace('\r', '')
        return(complete_string)

    def read_all_pressures(self):
        """ Read pressure from all sensors """
        pressures = [-3]
        error = 1
        while (error > 0) and (error < 10):
            pressure_string = self.xgs_comm("0F")
            if len(pressure_string) > 0:
                error = 0
                temp_pressure = pressure_string.replace(' ', '').split(',')
                pressures = []
                for press in temp_pressure:
                    if press == 'OPEN':
                        pressures.append(-1)
                    else:
                        try:
                            pressures.append((float)(press))
                        except ValueError:
                            pressures.append(-2)
            else:
                time.sleep(0.2)
                error = error +1
        return(pressures)


    def list_all_gauges(self):
        """ List all installed gauge cards """
        gauge_string = self.xgs_comm("01")
        gauges = ""
        for n in range(0, len(gauge_string), 2):
            gauge = gauge_string[n:n+2]
            if gauge == "10":
                gauges = gauges + str(n/2) + ": Hot Filament Gauge\n"
            if gauge == "FE":
                gauges = gauges + str(n/2) + ": Empty Slot\n"
            if gauge == "40":
                gauges = gauges + str(n/2) + ": Convection Board\n"
            if gauge == "3A":
                gauges = gauges + str(n/2) + ": Inverted Magnetron Board\n"
        return(gauges)

    def read_pressure(self, gauge_id):
        """ Read the pressure from a specific gauge """
        pressure = self.xgs_comm('02' + gauge_id)
        try:
            val = float(pressure)
        except ValueError:
            val = -1.0
        return(val)

    def filament_lit(self, gauge_id):
        """ Report if the filament of a given gauge is lid """
        filament = self.xgs_comm('34' + gauge_id) 
        return(int(filament))

    def emission_status(self, gauge_id):
        status = self.xgs_comm('32' + gauge_id)
        emission = status == '01'
        return emission

    def set_smission_off(self, gauge_id):
        """ Turn off emission from a given gauge """
        self.xgs_comm('30' + gauge_id)
        time.sleep(0.1)
        return self.emission_status(gauge_id)

    def set_emission_on(self, gauge_id, filament):
        """ Turn on emission for  a given gauge """
        if filament == 1:
            command = '31'
        if filament == 2:
            command = '33'
        self.xgs_comm(command + gauge_id)
        return self.emission_status(gauge_id)

    def read_software_version(self):
        gauge_string = self.xgs_comm("05")
        return(gauge_string)

    def read_pressure_unit(self):
        """ Read which pressure unit is used """
        gauge_string = self.xgs_comm("13")
        unit = gauge_string.replace(' ','')
        if unit == "00":
            unit = "Torr"
        if unit == "01":
            unit = "mBar"
        if unit == "02":
            unit = "Pascal"
        return(unit)


if __name__ == '__main__':
    xgs = XGS600Driver()
    for i in range(0, 20):
        print xgs.read_all_pressures()
    #print xgs.read_pressure_unit()

    #xgs.set_emission_on('I1',1)
    #time.sleep(0.2)
    #print xgs.read_pressure('I1')
    #time.sleep(0.2)
    #print xgs.emission_status('I1')
    #print xgs.read_pressure('I1')
