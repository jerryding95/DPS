import subprocess
from pathlib import Path
from DPS.config import *
import time

TEMPT_PATH = Path('/home/cc/tmp/')

# run `cmd' on `config.NODE_COUNT' worker nodes
def runRemoteCmd(cmd, wait=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE):
    out_list=[]
    # for i in range(1, config.NODE_COUNT+1):
    for i in config.EXP_NODES:
        host = "slave" + str(i)
        process = subprocess.Popen(["ssh", "-f", host, cmd], stdout=stdout,stderr=stderr)
        if wait:
            print(f'Worker {i}: {cmd}')
            out, err = process.communicate()
            out_list.append(out)
    return out_list


# kill the `name' process on `config.NODE_COUNT' worker nodes
def killProcess(name='perf', sudo=False):
    cmd = 'pkill -f '+name
    if sudo:    cmd = 'sudo '+cmd
    runRemoteCmd(cmd, wait=True)
    return True


# check if the `name' process is running on `config.NODE_COUNT' nodes
# Return: a config.NODE_COUNT-length list consisting of True's or False's
def checkProcess(name='perf'):
    flags = []

    cmd = "ps -A | grep "+name
    for i in range(1, config.NODE_COUNT+1):

        host = "slave" + str(i)
        process = subprocess.Popen(["ssh", host, cmd], stdout=subprocess.PIPE)
        out, err = process.communicate()
        if len(out.splitlines())>0:
            flags.append(True)
        if len(flags)<i:
            flags.append(False)

    return flags

def mkdir(pname, sudo=False):
    cmd = ["mkdir" pname]
    cmd = ["sudo"]+cmd if sudo else cmd
    subprocess.Popen(cmd, stdout=stdout,stderr=stderr)
    return

def mkdir_clients(pname, wait=True, sudo=False):
    cmd = f"mkdir {pname}"
    cmd = "sudo "+cmd if sudo else cmd
    for i in config.EXP_NODES:
        host = "slave" + str(i)
        process = subprocess.Popen(["ssh", "-f", host, cmd], stdout=stdout,stderr=stderr)
        if wait:
            process.communicate()
    return

# Clean Scheduling Affinity and Perf logfiles
def cleanFiles(filenames = ['perfRecord','affinity_log.txt']):
    process=process=subprocess.Popen(('rm -r '+str(TEMPT_PATH)).split(), stdout=subprocess.PIPE)
    out, err = process.communicate()
    for i in range (1, config.NODE_COUNT+1):
        cmd = 'rm '+' '.join(filenames)
        host = 'slave'+str(i)
        process = subprocess.Popen(['ssh', host, cmd], stdout=subprocess.PIPE)
        out, err = process.communicate()
    return 1


def start_spark(ind, benchmark, parallelism):
    print(f'Starting spark app {benchmark} on master{ind}')

    cmd = f'{Path().absolute()}/run_hibench.sh {benchmark} {parallelism}'
    host = f'master{ind}'

    p = subprocess.Popen(["ssh", host, cmd], stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    print(f'Spark started on master{ind}')

    o,_ = p.communicate()
    duration = float(o.decode('ascii').split('\n')[-2].split()[-1])
    return duration

def start_npb(ind, benchmark):

    npb_class = config.NPB_CLASS[benchmark]
    npb_np = config.NPB_NPERNODE[benchmark]
    exectable = str(config.NPB_PATH.joinpath(f'bin/{benchmark}.{npb_class}.x'))
    hostfile = str(config.NPB_PATH.joinpath(f'nodes'))
    add_key_cmd = 'eval `ssh-agent -s`; ssh-add /home/cc/.ssh/*.pem;'
    cmd = add_key_cmd + f'mpiexec -npernode {npb_np} --hostfile {hostfile} {exectable}'
    host = f'master{ind}'

    print(f'Starting NAS parallel benchmark {benchmark} on master{ind}')
    start_time = time.time()
    p = subprocess.Popen(["ssh", host, cmd], stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    o,_ = p.communicate()
    print(f'NPB {benchmark} finished on worker{ind}')
    end_time = time.time()

    duration = end_time - start_time
    return duration


def end_monitoring(keywords, stdout_arr=[]):
    print('Application finished, ending monitoring...')
    for keyword in keywords:
        killProcess(keyword, sudo=True)
        print(keyword, checkProcess(keyword))
    for f in stdout_arr:
        f.close()
    print('Monitoring ended')

class Sentinel:
    def __init__(self, count):
        self._sentinel_arr = [False for _ in range(count)]

    def get(self):
        return self._sentinel_arr

    def set(self, ind):
        self._sentinel_arr[ind] = not self._sentinel_arr[ind]
        return