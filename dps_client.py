import argparse
import numpy as np
from DPS.config import *
from DPS.dps import DPS_worker
RAPL_CAP_ARR = np.ones(2)*config.TDP


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cap', type=int, required=False, default=165)
    args = parser.parse_args()

    config.TDP = args.cap
    worker = DPS_worker()
    worker.exec()