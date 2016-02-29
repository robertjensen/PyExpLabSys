# pylint: disable=R0913,W0142,C0103

""" Temperature controller """
import time
import threading
import socket
import curses
import PyExpLabSys.auxiliary.pid as PID
import PyExpLabSys.drivers.cpx400dp as cpx
import PyExpLabSys.drivers.isotech_ips as ips
from PyExpLabSys.common.sockets import DateDataPullSocket
from PyExpLabSys.common.sockets import DataPushSocket
import wiringpi2 as wp # pylint: disable=F0401

class PulseHeater(threading.Thread):
    """ PWM class for simple heater """
    def __init__(self):
        threading.Thread.__init__(self)
        wp.wiringPiSetup()

        wp.pinMode(0, 1)
        wp.pinMode(1, 1)

        self.dc = 0
        self.quit = False

    def set_dc(self, dc):
        """ Set the duty cycle """
        self.dc = dc

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1)
        steps = 500
        state = False
        data = 'raw_wn#20:bool:'
        while not self.quit:
            for i in range(0, steps):
                if (1.0*i/steps < self.dc) and (state is False):
                    #wp.digitalWrite(0, 1)
                    #wp.digitalWrite(1, 1)
                    sock.sendto(data + 'True', ('rasppi33', 8500))
                    #received = sock.recv(1024)
                    state = True
                if (1.0*i/steps < self.dc) and (i>5):
                    wp.digitalWrite(0, 1)
                    wp.digitalWrite(1, 1)

                if (1.0*i/steps > self.dc) and (state is True):
                    wp.digitalWrite(0, 0)
                    wp.digitalWrite(1, 0)
                    sock.sendto(data + 'False', ('rasppi33', 8500))
                    #received = sock.recv(1024)
                    state = False
                time.sleep(15.0 / steps)
        sock.sendto(data + 'False', ('rasppi33', 9999))

class CursesTui(threading.Thread):
    """ Text user interface for furnace heating control """
    def __init__(self, heating_class, heater):
        threading.Thread.__init__(self)
        self.start_time = time.time()
        self.quit = False
        self.hc = heating_class
        self.heager = heater
        self.screen = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(False)
        self.screen.keypad(1)
        self.screen.nodelay(1)

    def run(self):
        while not self.quit:
            self.screen.addstr(3, 2, 'Running')
            val = self.hc.pc.setpoint
            self.screen.addstr(9, 40, "Setpoint: {0:.2f}C  ".format(val))
            val = self.hc.pc.temperature
            try:
                self.screen.addstr(9, 2, "Temeperature: {0:.1f}C  ".format(val))
            except ValueError:
                self.screen.addstr(9, 2, "Temeperature: -         ".format(val))
            val = self.hc.voltage * 2 # Two locked output channels
            self.screen.addstr(10, 2, "Wanted Voltage: {0:.2f}V  ".format(val))
            val = self.hc.actual_voltage * 2 # Two locked output channels
            self.screen.addstr(10, 40, "Actual Voltage: {0:.2f}V  ".format(val))
            val = self.hc.actual_current
            self.screen.addstr(11, 40, "Actual Current: {0:.2f}A  ".format(val))
            val = self.hc.actual_current * self.hc.actual_voltage * 2
            self.screen.addstr(12, 40, "Actual Power: {0:.2f}W  ".format(val))
            val = self.hc.pc.pid.setpoint
            self.screen.addstr(11, 2, "PID-setpint: {0:.2f}C  ".format(val))
            val = self.hc.pc.pid.integrated_error()
            self.screen.addstr(12, 2, "PID-error: {0:.3f}   ".format(val))
            val = self.hc.pc.pid.proportional_contribution()
            self.screen.addstr(13, 2, "P-term: {0:.3f}   ".format(val))
            val = self.hc.pc.pid.integration_contribution()
            self.screen.addstr(14, 2, "i-term: {0:.3f}   ".format(val))
            val = time.time() - self.start_time
            self.screen.addstr(18, 2, "Run time: {0:.0f}s".format(val))
            self.screen.addstr(19, 2, "Message:" + self.hc.pc.message)
            self.screen.addstr(20, 2, "Message:" + self.hc.pc.message2)

            n = self.screen.getch()
            if n == ord('q'):
                self.hc.quit = True
                self.quit = True
            if n == ord('i'):
                self.hc.pc.update_setpoint(self.hc.pc.setpoint + 1)
            if n == ord('d'):
                self.hc.pc.update_setpoint(self.hc.pc.setpoint - 1)

            self.screen.refresh()
            time.sleep(0.2)
        self.stop()

    def stop(self):
        """ Clean up console """
        curses.nocbreak()
        self.screen.keypad(0)
        curses.echo()
        curses.endwin()


class PowerCalculatorClass(threading.Thread):
    """ Calculate the wanted amount of power """
    def __init__(self, pullsocket, pushsocket):
        threading.Thread.__init__(self)
        self.pullsocket = pullsocket
        self.pushsocket = pushsocket
        self.power = 0
        self.setpoint = 50
        self.pid = PID.PID()
        self.pid.pid_p = 1
        self.pid.pid_i = 0.00075
        self.pid.p_max = 60
        self.update_setpoint(self.setpoint)
        self.quit = False
        self.temperature = None
        self.ramp = None
        self.message = '**'
        self.message2 = '*'

    def read_power(self):
        """ Return the calculated wanted power """
        return(self.power)

    def update_setpoint(self, setpoint=None):
        """ Update the setpoint """
        self.setpoint = setpoint
        self.pid.update_setpoint(setpoint)
        self.pullsocket.set_point_now('setpoint', setpoint)
        return setpoint

    def run(self):
        data_temp = 'vhp_T_reactor_outlet#raw'
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1)
        while not self.quit:
            self.pullsocket.set_point_now('pid_p', self.pid.proportional_contribution())
            self.pullsocket.set_point_now('pid_i', self.pid.integration_contribution())
            self.pullsocket.set_point_now('pid_e', self.pid.integrated_error())

            sock.sendto(data_temp, ('localhost', 9000))
            received = sock.recv(1024)
            self.temperature = float(received[received.find(',') + 1:])
            self.power = self.pid.wanted_power(self.temperature)

            #  Handle the setpoint from the network
            try:
                setpoint = self.pushsocket.last[1]['setpoint']
                new_update = self.pushsocket.last[0]
                self.message = str(new_update)
            except (TypeError, KeyError): #  Setpoint has never been sent
                self.message = str(self.pushsocket.last)
                setpoint = None
            if setpoint is not None:
                self.update_setpoint(setpoint)
            time.sleep(1)


class HeaterClass(threading.Thread):
    """ Do the actual heating """
    def __init__(self, power_calculator, pullsocket, ps, ps_isotech):
        threading.Thread.__init__(self)
        self.pc = power_calculator
        self.heater = ps
        self.heater_isotech = ps_isotech
        self.heater.output_status(True)
        self.heater_isotech.set_output_voltage(0)
        self.heater_isotech.set_relay_status(True)
        self.pullsocket = pullsocket
        self.voltage = 0
        self.actual_voltage = 0
        self.actual_current = 0
        self.quit = False

    def run(self):
        time.sleep(0.05)
        while not self.quit:
            self.voltage = self.pc.read_power()
            self.pullsocket.set_point_now('voltage', self.voltage)
            if self.voltage < 10:
                self.heater_isotech.set_output_voltage(self.voltage*2)
                self.heater.set_voltage(0)
            else:
                self.heater_isotech.set_output_voltage(2 * 10)
                self.heater.set_voltage(self.voltage-10)
            self.actual_voltage = self.heater.read_actual_voltage()
            self.actual_current = self.heater.read_actual_current()
            time.sleep(0.5)
        self.heater.set_voltage(0)
        self.heater.output_status(False)

CPX = cpx.CPX400DPDriver(1, device='/dev/ttyACM0', interface='serial')
ISOTECH = ips.IPS('/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0')

Pullsocket = DateDataPullSocket('vhp_temp_control',
                                ['setpoint', 'dutycycle','pid_p', 'pid_i', 'pid_e'], 
                                timeouts=[999999, 3.0, 3.0, 3.0, 3.0],
                                port=9001)
Pullsocket.start()

Pushsocket = DataPushSocket('vhp_push_control', action='store_last')
Pushsocket.start()

P = PowerCalculatorClass(Pullsocket, Pushsocket)
P.daemon = True
P.start()

H = HeaterClass(P, Pullsocket, CPX, ISOTECH)
H.start()

T = CursesTui(H, CPX)
T.daemon = True
T.start()

