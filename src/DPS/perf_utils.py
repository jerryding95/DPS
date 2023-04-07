import numpy as np
import sys
import time
import csv
from config import *
from process_utils import *
from pathlib import Path
from datetime import datetime

# generate perf stat command with `events' and write with `interval' into `output'
def genPerfCmd(events, output = 'perfRecord', interval = config.PERF_INTERVAL):
    cmd = "perf stat -a --per-socket -e "
    for event in events:
        cmd += event + ","
    cmd = cmd[:-1] + " "
    cmd += "-x, -I " + str(interval) + " "
    cmd += "-o " + output + " "

    return cmd

### Perf Monitoring ###
def start_perf():
    # start perf processes
    runRemoteCmd(genPerfCmd(config.EVENTS))

    # wait for the processes to start
    time.sleep(1)

    #check if processes are up
    flags = checkProcess('perf')
    print(flags)
    if not all(flag for flag in flags):
        killProcess('perf')
        sys.exit('Process starting error. Try again.')
    else:
        print('Perf processes successfully started.')
    return True

# collect the perf monitor records from worker nodes
def collectPerfRecords(filename='perfRecord'):

    print('Fetching perf monitoring files from workers ...')

    process=subprocess.Popen(('mkdir '+str(config.TEMPT_PATH)).split(), stdout=subprocess.PIPE)
    out, err = process.communicate()
    for i in config.EXP_NODES:
        cmd = 'scp'
        host_dest = 'slave'+str(i)+':~/'+filename
        cp_dest = config.TEMPT_PATH.joinpath(filename+str(i))
        process = subprocess.Popen([cmd, host_dest, cp_dest], stdout=subprocess.PIPE)
        out, err = process.communicate()

    print('Finished fetching.')

    return 1

# convert xx:xx:xx to x seconds since 1971-1-1
def convertTime(time):
    t = datetime(datetime.now().year,datetime.now().month,datetime.now().day,\
            int(time[0:2]),int(time[3:5]),int(time[6:]))
    return t.timestamp()

# intergrate perf outputs to a CSV file
def genPerfReport(start, end, filename='perfRecord', outfile='perf_data.csv', start_ind=1, end_ind=config.NODE_COUNT):

    print('Generating perf monitoring record ...')

    # Prepare two header lines
    header1 = []
    header2 = []
    for i in range(start_ind, end_ind+1):
        header1 += ['Worker'+str(i), 'S0']+['' for j in range(len(config.EVENTS)-1)]
        header1 += ['S1']+['' for j in range(len(config.EVENTS)-1)]
        header2 += ['Time'] + config.EVENTS + config.EVENTS

    # Read data
    data=[]

    for i in range (start_ind, end_ind+1):
        subdata=[[] for j in range(2*len(config.EVENTS)+1)]
        
        with open(config.TEMPT_PATH.joinpath(filename+str(i))) as f:
            reader = csv.reader(f, skipinitialspace=True, delimiter=' ')
            lines = f.readlines()

        # Get the start time in the first line
        l0 = lines[0].split()
        start_time = convertTime(l0[6])


        lines = lines[2:]
        count = len(lines)//(2*len(config.EVENTS))
        for i in range(count):
            base_ind = i*2*len(config.EVENTS)
            time = float(lines[base_ind].split(',')[0])
            subdata[0].append(time)

            for j in range(2*len(config.EVENTS)):
                line = lines[base_ind+j].split(',')
                metric = float(line[3])
                subdata[j+1].append(metric)



        # Cut off tails
        length = min([len(d) for d in subdata])
        subdata = np.array([d[:length] for d in subdata])

        # Add the start time to the time column
        subdata[0] = np.array(subdata[0])+start_time

        # Exclude time before and after running the workload
        subdata = (subdata.T[np.logical_and(subdata.T[:,0] >= start, subdata.T[:,0] <= end)]).T.tolist()

        data += subdata

    # Cut off tails
    length = min([len(subdata) for subdata in data])
    data = np.array([column[:length] for column in data]).T
    
    # Write data into file
    with open(outfile, mode='w') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow(header1)
        writer.writerow(header2)
        for row in data:
            writer.writerow(row)

    print('Finished generating.')

    return data

######################


# For bandits agent

def get_perf_cmd(events=config.EVENTS, timeout=10):
    cmd = "perf stat -a --per-socket -e "
    for event in events:
        cmd += event + ","
    cmd = cmd[:-1] + " "
    cmd += f"-x, -I {timeout*1000}"

    return cmd

def start_agent_perf(cmd):
    p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    return p

def extract_perf_metric(raw_data):
    t = float(raw_data[0][0])
    data = {'S0':{},'S1':{}}
    for d in raw_data:
        socket = d[1]
        name = d[5]
        metric = d[3]
        data[socket][name]=float(metric)
    res = np.zeros((2,6))
    for i in range(2):
        socket = 'S'+str(i)
        res[i,0] = data[socket]['LLC-load-misses']/data[socket]['LLC-loads']
        res[i,1] = data[socket]['context-switches']/t
        res[i,2] = data[socket]['page-faults']/t
        res[i,3] = data[socket]['branch-load-misses']/data[socket]['branch-loads']
        res[i,4] = data[socket]['dTLB-load-misses']/data[socket]['dTLB-loads']
        res[i,5] = data[socket]['inst_retired.any']/data[socket]['cpu-cycles']
    return res

def get_perf_metrics(p):
    raw_data = []
    for _ in range(len(config.EVENTS)*2):
        raw_data.append(p.stderr.readline().decode('ascii').split(','))
    p.terminate()

    data = extract_perf_metric(raw_data)

    return data





