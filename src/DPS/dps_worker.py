import argparse
import numpy as np
from config import *
from dps import DPS_worker
RAPL_CAP_ARR = np.ones(2)*config.TDP


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cap', type=int, required=False, default=165)
    args = parser.parse_args()

    config.TDP = args.cap
    worker = DPS_worker()
    worker.exec()























    # parser = argparse.ArgumentParser()
    # parser.add_argument('--cap', type=int, required=False, default=165)
    # args = parser.parse_args()

    # config.TDP = args.cap
    # RAPL_CAP_ARR = RAPL_CAP_ARR * 0 + config.TDP


    # fd0, fd1 = open_msr(0), open_msr(1)
    # power_unit0, power_unit1 = read_power_unit(fd0), read_power_unit(fd1)
    # energy_unit0, energy_unit1 = read_energy_unit(fd0), read_energy_unit(fd1)
    # RAPL_CAP_ARR[0] = read_pkg_cap(fd0, power_unit0)
    # RAPL_CAP_ARR[1] = read_pkg_cap(fd1, power_unit1)

    # print('Wating for master connection...')
    # s = socket.socket()
    # # s.bind((socket.gethostname(), config.SOCKET_PORT))
    # s.bind(('', config.SOCKET_PORT))
    # s.listen(1)
    # conn, addr = s.accept()
    # print('Master connected.')
    
    # while True:

    #     print('\n[New Iteration]')
    #     # Receive signal
    #     print('Wating for message from master...')
    #     mssg = ''
    #     while not mssg:
    #         mssg = conn.recv(6)
    #     print(f'Message received: {mssg}')
    #     mssg = int(mssg, 16)


    #     # End if application is finished

    #     if mssg == 0xFFFFFF:
    #         print('Ending message received, exiting...')
    #         break

    #     # Decode signal
    #     change0, change1 = mssg>>23, (mssg>>11)&0x1
    #     RAPL_CAP_ARR[0], RAPL_CAP_ARR[1] = (mssg>>12)&0x7FF, mssg&0x7FF

    #     # Change cap
    #     if change0:
    #         print('Changing s_0 rapl cap to ', RAPL_CAP_ARR[0])
    #         set_socket_pkg_power_cap(fd0, RAPL_CAP_ARR[0], power_unit0)

    #     if change1:
    #         print('Changing s_1 rapl cap to ', RAPL_CAP_ARR[1])
    #         set_socket_pkg_power_cap(fd1, RAPL_CAP_ARR[1], power_unit1)

    #     # Read rapl
    #     print('Reading rapl pkg power...')
    #     start_power0, start_power1 = read_pkg_energy(fd0, energy_unit0), read_pkg_energy(fd1, energy_unit1)
    #     time.sleep(1)
    #     end_power0, end_power1 = read_pkg_energy(fd0, energy_unit0), read_pkg_energy(fd1, energy_unit1)
    #     power0, power1 = round(end_power0 - start_power0), round(end_power1 - start_power1)
    #     if power0 < 0:
    #         power0 += int(energy_unit0 * 0xFFFFFFFF)
    #     if power1 < 0:
    #         power1 += int(energy_unit1 * 0xFFFFFFFF)
    #     print('Rapl pkg power: ', power0, power1)

    #     # Send rapl to master
    #     mssg = f'{power0:0{3}x}{power1:0{3}x}'
    #     print(f'Sending power reading {mssg} to master...')
    #     conn.send(mssg.encode('utf-8'))
    #     print('Power readings sent')

    # s.close()