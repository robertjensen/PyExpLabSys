# pylint: disable=no-member
""" MetaLogger program """
from __future__ import print_function
import os
import sys
import time
import datetime
try:
    import Queue as queue
except ImportError:
    import queue
import PyExpLabSys.common.database_saver as database_saver
#import PyExpLabSys.drivers.pfeiffer_qmg420 as qmg420
#import PyExpLabSys.drivers.pfeiffer_qmg422 as qmg422
import PyExpLabSys.apps.qms.qms as ms
import PyExpLabSys.apps.qms.qmg_status_output as qmg_status_output
import PyExpLabSys.apps.qms.qmg_meta_channels as qmg_meta_channels
from PyExpLabSys.common.sockets import DateDataPullSocket#, LiveSocket
from PyExpLabSys.common.utilities import get_logger
from PyExpLabSys.common.utilities import activate_library_logging
from PyExpLabSys.common.supported_versions import python2_and_3
BASEPATH = os.path.abspath(__file__)[:os.path.abspath(__file__).find('PyExpLabSys')]+'PyExpLabSys'
sys.path.append(BASEPATH + '/PyExpLabSys/machines/' + sys.argv[1])
import settings # pylint: disable=wrong-import-position
python2_and_3(__file__)

LOGGER = get_logger('MetaChannelLogger', level='warning', file_log=True,
                    file_name='MetaChannelLogger.txt', terminal_log=False,
                    email_on_warnings=False, email_on_errors=False,
                    file_max_bytes=104857600, file_backup_count=5)

#activate_library_logging('PyExpLabSys.drivers.pfeiffer_qmg422',
#                         logger_to_inherit_from=LOGGER)
activate_library_logging('PyExpLabSys.apps.qms.qmg_status_output',
                         logger_to_inherit_from=LOGGER)
activate_library_logging('PyExpLabSys.apps.qms.qmg_meta_channels',
                         logger_to_inherit_from=LOGGER)
activate_library_logging('PyExpLabSys.apps.qms.qms',
                         logger_to_inherit_from=LOGGER)

try:
    from local_channels import Local
    LOCAL_READER = Local()
    LOCAL_READER.daemon = True
    LOCAL_READER.start()
except ImportError:
    pass


class MetaLogger(object):
    """ User interface to mass spec code """
    def __init__(self):
        sql_queue = queue.Queue()
        self.data_saver = database_saver.SqlSaver(settings.username,
                                                  settings.username, sql_queue)
        self.data_saver.start()
        print('self data saver')
        #if settings.qmg == '420':
        #    self.qmg = None  #qmg420.qmg_420(settings.port)
        #if settings.qmg == '422':
        #    print(settings.port)
        self.qmg = None  #qmg422.qmg_422(port=settings.port, speed=settings.speed)

        #try:
        #    livesocket = LiveSocket(settings.name + '-mass-spec', ['qms-value'])
        #    livesocket.start()
        #except:
        #    livesocket = None

        pullsocket = DateDataPullSocket(settings.name + '-mass-spec', ['qms-value'])
        pullsocket.start()

        self.qms = ms.QMS(self.qmg, sql_queue, chamber=settings.chamber,
                          credentials=settings.username,# livesocket=livesocket,
                          pullsocket=pullsocket)
        print('self QMS MS')
        #self.qmg.reverse_range = settings.reverse_range
        try:
            self.printer = qmg_status_output.QmsStatusOutput(self.qms,
                                                         sql_saver_instance=self.data_saver)
        except KeyError as e:
            print(e)
        print('self printer MS')
        self.printer.start()

    def __del__(self):
        self.printer.stop()

    def logging(self, channel_list='channel_list'):
        """ start logging of meta data """
        print('start logging')
        timestamp = datetime.datetime.now()
        print(BASEPATH + '/PyExpLabSys/machines/' + sys.argv[1] + '/channel_lists/' + channel_list + '.txt')

        qms_channel_list = self.qms.read_ms_channel_list(BASEPATH + '/PyExpLabSys/machines/' +
                                                         sys.argv[1] + '/channel_lists/' +
                                                         channel_list + '.txt')
        meta_udp = qmg_meta_channels.MetaChannels(self.qms, timestamp, qms_channel_list)
        meta_udp.daemon = True
        meta_udp.start()
        self.printer.meta_channels = meta_udp

def sleep(self, duration):
        """ Sleep for a while and print output """
        msg = 'Sleeping for {} seconds..'
        for i in range(duration, 0, -1):
            self.qms.operating_mode = msg.format(i)
            time.sleep(1)
        self.qms.operating_mode = 'Idling'

if __name__ == '__main__':
 #   try:
        # Initialize QMS
    print('here erere')
    ML = MetaLogger()
        #MS.sem_and_filament(True, 1800)
        #MS.sleep(10)

        # Choose and start measurement(s)
        #MS.leak_search(speed=8)
    print('here 1')
    ML.sleep(5)
    print('here 2')
    ML.logging()
    print('here 3')
    ML.sleep(50)

        #MS.mass_scan(0, 50, 'flow6', amp_range=-11)
        #MS.mass_scan(0, 50, 'After power line cleanup', amp_range=-11)

        #MS.mass_scan(0, 50, 'Background scan -11', amp_range=-11)
        #MS.mass_scan(0, 50, 'Background scan -9', amp_range=-9)
        #MS.mass_scan(0, 50, 'Background scan -7', amp_range=-7)
#    except e:
#        print(e)
#        ML.printer.stop()
#        raise
#    finally:
#        ML.printer.stop()
