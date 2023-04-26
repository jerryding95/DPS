import numpy as np
import csv
from DPS.config import *
from DPS.process_utils import *
from pathlib import Path
import os
import time
import argparse
import subprocess

### RAPL ###

MSR_RAPL_POWER_UNIT = 0x606

## Package RAPL Domain ##
MSR_PKG_POWER_LIMIT = 0x610
MSR_PKG_ENERGY_STATUS = 0x611
MSR_PKG_PERF_STATUS = 0x613
MSR_PKG_POWER_INFO = 0x614

## DRAM RAPL Domain ##
MSR_DRAM_POWER_LIMIT = 0x618
MSR_DRAM_ENERGY_STATUS = 0x619
MSR_DRAM_PERF_STATUS = 0x61B
MSR_DRAM_POWER_INFO = 0x61C



def start_rapl(outfile=Path('/home/cc/RAPL/PowerResults.txt')):
    runRemoteCmd('sudo '+str(config.RAPL_PATH)+' '+str(outfile),wait=False)

def collectRaplRecords(file=Path('/home/cc/RAPL/PowerResults.txt')):

    print('Fetching RAPL monitoring files from workers ...')

    process=subprocess.Popen(['mkdir',config.TEMPT_PATH], stdout=subprocess.PIPE)
    out, err = process.communicate()
    for i in config.EXP_NODES:
        cmd = 'scp'
        host_dest = 'slave'+str(i)+':'+str(file)
        filename=Path(file).name
        cp_dest = config.TEMPT_PATH.joinpath(str(i)+'_'+filename)
        process = subprocess.Popen([cmd, host_dest, cp_dest], stdout=subprocess.PIPE)
        out, err = process.communicate()

    print('Finished fetching.')
    
    return 1
def gen_mab_rapl_file(checkpoint, filename = 'trace.out', outfile = 'raplFile'):

    for i in range(1,5):
        data = np.loadtxt(config.RECORD_PATH.joinpath(f'checkpoint{checkpoint}/slave{i}/{filename}'), \
            delimiter=',')
        data = data[:,[0,4,5,6,7]]
        data[:,[4,2]] = data[:,[2,4]]
        np.savetxt(config.TEMPT_PATH.joinpath(f'{i}_{outfile}'),data,fmt='%.6f')


def genRaplReport(start, end, filename='PowerResults', outfile='rapl_data.csv', start_ind=1, end_ind=config.NODE_COUNT):

    print('Generating RAPL monitoring record ...')

    # Prepare two header lines
    header1 = []
    header2 = []
    for i in range(start_ind, end_ind+1):
        header1 += [f'worker{i}','','','','']
        header2 += ['time','s0_power(\u03BCW)','s1_power(\u03BCW)',\
                    's0_dram_power(\u03BCW)','s1_dram_power(\u03BCW)']

    # Read in data
    # data = [[] for i in range(3*NODE_COUNT)]
    data=[]
    for i in range(start_ind, end_ind+1):
        subdata=[]
        dest = config.TEMPT_PATH.joinpath(str(i)+'_'+filename)
        with open(dest) as f:
            reader = csv.reader(f, skipinitialspace=True, delimiter=' ')
            for row in reader:
                subdata.append([float(k) for k in row])

        # Exclude time before and after running the workload
        subdata = np.array(subdata)
        subdata = subdata[np.logical_and(subdata[:,0] >= start, subdata[:,0] <= end)].T.tolist()

        data+=subdata

    # Cut off tails
    length = min([len(data[i]) for i in range(len(data))])
    data=[column[:length] for column in data]
    # print([len(arr) for arr in data])

    # Write to output file
    data = np.array(data)
    with open(outfile, mode='w') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow(header1)
        writer.writerow(header2)
        for row in data.T:
            writer.writerow(row)

    print('Finished generating.')

    return data


def open_msr(socket):
    msr_filename = f'/dev/cpu/{socket}/msr'
    
    try:
        fd = os.open(msr_filename, os.O_RDWR)
    except OSError:
        print(f'rdmsr: Error opening {msr_filename}')
        exit()

    return fd


def read_msr(fd, which):
    data = os.pread(fd, 8, which)
    return int.from_bytes(data, byteorder='little')


def write_msr(fd, which, data):
    d = data.to_bytes(8, 'little')
    os.pwrite(fd, d, which)

def read_power_unit(fd):
    raw_unit = read_msr(fd, MSR_RAPL_POWER_UNIT)
    unit = 0.5**float(raw_unit&0xf)
    return unit

def read_energy_unit(fd):
    raw_unit = read_msr(fd, MSR_RAPL_POWER_UNIT)
    unit = 0.5**float((raw_unit>>8)&0x1f)
    return unit

def read_pkg_energy(fd, unit):
    return read_msr(fd, MSR_PKG_ENERGY_STATUS)*unit

def read_dram_energy(fd, unit):
    return read_msr(fd, MSR_DRAM_ENERGY_STATUS)*unit


def get_avg(filename):
    with open(filename) as f:
        data_list = list(csv.reader(f))
    data = np.array(data_list[2:],dtype=np.float64)
    mask = np.ones(data.shape[1],dtype=bool)
    index = [i*5 for i in range(data.shape[1]//5)]
    mask[index] = False
    data = data[:,mask].T
    for subdata in data:
        for i, value in enumerate(subdata):
            if value < 0: subdata[i] = (subdata[i-1]+subdata[i+1])/2
    avg = np.average(data, axis=1)
    return avg

def static_profile(filename='static.csv',time_range=600):
    start_rapl(outfile=config.RECORD_PATH.joinpath('raplFile'))
    start_time = time.time()
    time.sleep(time_range)
    end_time = time.time()
    killProcess('Rapl', sudo=True)
    print(checkProcess('Rapl'))
    collectRaplRecords(config.RECORD_PATH.joinpath('raplFile'))
    genRaplReport(filename='raplFile',outfile=config.RECORD_PATH.joinpath('RAPL_'+filename), start = start_time, end = end_time)

def read_pkg_cap(fd, unit):
    raw_val = read_msr(fd, MSR_PKG_POWER_LIMIT)
    val = raw_val & 0x0000000000007FFF
    return val*unit

def set_socket_pkg_power_cap(fd, cap, unit):
    set_point = int(cap/unit)
    reg = read_msr(fd, MSR_PKG_POWER_LIMIT)
    reg = (reg & 0xFFFFFFFFFFFF0000) | set_point | 0x8000
    write_msr(fd, MSR_PKG_POWER_LIMIT, reg)
    return


def set_pkg_power_cap(cap0,cap1):
    caps = [cap0,cap1]
    for i in range(2):
        fd = open_msr(i)
        power_unit = read_power_unit(fd)
        set_point = int(caps[i]/power_unit)
        reg = read_msr(fd, MSR_PKG_POWER_LIMIT)
        reg = (reg & 0xFFFFFFFFFFFF0000) | set_point | 0x8000
        write_msr(fd, MSR_PKG_POWER_LIMIT, reg)

def set_dram_power_cap(cap0,cap1):
    caps = [cap0,cap1]
    for i in range(2):
        fd = open_msr(i)
        power_unit = read_power_unit(fd)
        set_point = int(caps[i]/power_unit)
        reg = read_msr(fd, MSR_DRAM_POWER_LIMIT)
        reg = (reg & 0xFFFFFFFFFFFF0000) | set_point | 0x8000
        write_msr(fd, MSR_DRAM_POWER_LIMIT, reg)

def set_worker_pkg_power_cap(worker,cap0,cap1):
    host = f"slave{worker}"
    cmd = f'sudo python3 /home/cc/chameleon-files/rapl_utils.py set_pkg_power_cap {cap0} {cap1}'
    process = subprocess.Popen(["ssh", "-f", host, cmd], stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    process.communicate()
    return

def set_workers_pkg_power_cap(cap0,cap1):
    runRemoteCmd(f'sudo python3 {Path.home()}/DPS/src/DPS/rapl_utils.py set_pkg_power_cap {cap0} {cap1}', wait=True)

def set_workers_dram_power_cap(cap0,cap1):
    runRemoteCmd(f'sudo python3 {Path.home()}/DPS/src/DPS/rapl_utils.py set_dram_power_cap {cap0} {cap1}', wait=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('func', type=str)#, required=True)
    parser.add_argument('arg0', type=str)#, required=False)
    parser.add_argument('arg1', type=str)#, required=False)

    args = parser.parse_args()

    if args.func == 'static_profile':
        static_profile()
    elif args.func == 'set_pkg_power_cap':
        print(f'set_pkg_power_cap({float(args.arg0)},{float(args.arg1)})')
        set_pkg_power_cap(float(args.arg0),float(args.arg1))
    elif args.func == 'set_dram_power_cap':
        print(f'set_dram_power_cap({float(args.arg0)},{float(args.arg1)})')
        set_dram_power_cap(float(args.arg0),float(args.arg1))

# fd = open_msr(0)

# result = read_msr(fd, MSR_PKG_ENERGY_STATUS)
# print(result)