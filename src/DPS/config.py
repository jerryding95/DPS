from pathlib import Path

class config_type:
    def __init__(self):
        # Cluster and networking
        self.NODE_COUNT = 6
        self.CLUSTER_COUNT = 2
        self.CORE_COUNT = 384
        self.EXP_NODES = [1,2,3,4,5,6]
        self.EXP_IPS = ['10.52.2.243', '10.52.2.230', '10.52.3.118', '10.52.3.133', '10.52.3.111', '10.52.1.93']
        self.SLAVE_USER = "cc"

        # Benchmark
        self.HIBENCH_PATH = Path(f'{Path.home()}/HiBench/bin/workloads/')
        self.NPB_PATH = Path(f"{Path.home()}/NPB3.4.2/NPB3.4-MPI");
        self.NPB_CLASS = {'bt':'E', 'cg':'E', 'ep':'F', 'ft':'E', 'is':'E', 'lu':'E', 'mg':'E', 'sp':'E'}
        self.NPB_NPERNODE = {'bt':36, 'cg':32, 'ep':48, 'ft':32, 'is':32, 'lu':48, 'mg':32, 'sp':36}
        
        # Monitoring
        self.EVENTS = ['LLC-loads','LLC-load-misses','context-switches',\
            'page-faults','branch-loads','branch-load-misses',\
            'dTLB-loads','dTLB-load-misses','inst_retired.any','cpu-cycles']
        self.PERF_INTERVAL = 1000 # in ms
        self.RAPL_PATH = Path(f'{Path.home()}/RAPL/RaplPowerMonitor_1s')
        self.RECORD_PATH = Path(f'{Path.home()}/record')
        self.TEMPT_PATH = Path(f'{Path.home()}/tmp')

        # Networking in DPS
        self.SOCKET_PORT = 13425
        self.MESSAGE_START = b'1'
        self.MESSAGE_END = b'0'
        self.MESSAGE_OVER = b'2'


        self.NORM_TIME_WITH_NEW_AVG = True
        self.THRESHOLD_WITH_HALF_STD = False

        # Power spec
        self.TDP = 165
        self.MAX_POWER = 200
        self.MIN_POWER = 70

        # Kalman Filter parameters
        self.DERIV_THRESHOLD = 15
        self.PROCESS_NOISE = 5
        self.MEASUREMENT_NOISE = 10

        


config = config_type()
