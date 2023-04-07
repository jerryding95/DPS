from pathlib import Path

class config_type:
    def __init__(self):
        # Cluster and networking
        self.NODE_COUNT = 10
        self.CLUSTER_COUNT = 2
        self.CORE_COUNT = 384
        self.EXP_NODES = [1,2,3,4,5,6,7,8,9,10]
        self.EXP_IPS = ['10.52.3.217','10.52.2.253','10.52.2.169','10.52.0.19','10.52.3.51','10.52.2.118','10.52.2.211','10.52.3.38','10.52.3.156','10.52.2.226']
        self.SLAVE_USER = "cc"

        # Benchmark
        self.HIBENCH_PATH = Path('/home/cc/HiBench/bin/workloads/')
        self.NPB_PATH = Path("/home/cc/NPB3.4.2/NPB3.4-MPI");
        self.NPB_CLASS = {'bt':'D', 'cg':'E', 'ep':'E', 'ft':'E', 'is':'E', 'lu':'E', 'mg':'E', 'sp':'D'}
        self.NPB_NPERNODE = {'bt':36, 'cg':32, 'ep':48, 'ft':32, 'is':32, 'lu':48, 'mg':32, 'sp':36}
        
        # Monitoring
        self.EVENTS = ['LLC-loads','LLC-load-misses','context-switches',\
            'page-faults','branch-loads','branch-load-misses',\
            'dTLB-loads','dTLB-load-misses','inst_retired.any','cpu-cycles']
        self.PERF_INTERVAL = 1000
        self.RAPL_PATH = Path('/home/cc/RAPL/RaplPowerMonitor_1s')
        self.RECORD_PATH = Path('/home/cc/record')
        self.TEMPT_PATH = Path('/home/cc/tmp/')

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
