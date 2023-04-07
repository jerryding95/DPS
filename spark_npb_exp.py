import subprocess
import time
import threading 
import socket
import numpy as np
import sys
import argparse
from config import *
from rapl_utils import *
from perf_utils import *
from noise_utils import *
from slurm_utils import *
from process_utils import *
from dps import *


PARALLELISM = 384
BENCHMARK_HIBENCH = ['kmeans', 'lda', 'linear', 'lr', 'bayes', 'rf','gmm']
BENCHMARK_EQUAL = ['bt','sp']#list(config.NPB_CLASS)
BENCH_COUNTS = None
FINISHED = False


####### Cluster Executing Functions ######

def execute_cluster_pairs(ind, npb_bench, count, duration_file, scheduler):

	print(f'Executing clusters with mode: Pair, pair_count: {count}')
	global BENCH_COUNTS, FINISHED

	if ind == 1:
		while not FINISHED:
			print(f'Cluster {ind+1}: Starting {npb_bench}')
			app_start_time = time.time()
			duration = start_npb(ind+1, npb_bench)
			# time.sleep(3)
			# duration = 3
			app_end_time = time.time()
			with open(duration_file, 'a') as f:
				f.write(f'{npb_bench}, {app_start_time}, {app_end_time}, {duration}\n')

	else:
		for i,benchmark in enumerate(BENCHMARK_HIBENCH):
			while BENCH_COUNTS[i] < count:

				outstr = "Progress: "
				for b,c in zip(BENCHMARK_HIBENCH,BENCH_COUNTS):
					outstr += f'{b}: {c}/{count}, '
				print(outstr[:-2])
				BENCH_COUNTS[i] += 1

				print(f'Cluster {ind+1}: Starting {benchmark}')
				app_start_time = time.time()
				duration = start_spark(ind+1, benchmark, PARALLELISM)
				# time.sleep(3)
				# duration = 3
				app_end_time = time.time()

				with open(duration_file, 'a') as f:
					f.write(f'{benchmark}, {app_start_time}, {app_end_time}, {duration}\n')

				
		FINISHED = True

	scheduler.sentinel_set(ind)
	return

def execute_cluster_equal(ind, count, duration_file, scheduler):
	print(f'Executing Spark clusters with mode: Equal, count: {count}')
	global BENCH_COUNTS

	if ind == 1:
		time.sleep(5)
	for i,benchmark in enumerate(BENCHMARK_EQUAL):
		while BENCH_COUNTS[i] < count:

			outstr = "Before Progress: "
			for b,c in zip(BENCHMARK_EQUAL,BENCH_COUNTS):
				outstr += f'{b}: {c}/{count}, '
			print(outstr[:-2])
			BENCH_COUNTS[i] += 1

			print(f'Cluster {ind+1}: Starting {benchmark}')
			app_start_time = time.time()
			if benchmark in config.NPB_CLASS:
				duration = start_npb(ind+1, benchmark)
			else:
				duration = start_spark(ind+1, benchmark, PARALLELISM)
			app_end_time = time.time()

			with open(duration_file, 'a') as f:
				f.write(f'{benchmark}, {app_start_time}, {app_end_time}, {duration}\n')

			

			outstr = "After Progress: "
			for b,c in zip(BENCHMARK_EQUAL,BENCH_COUNTS):
				outstr += f'{b}: {c}/{count}, '
			print(outstr[:-2])
		print(f'###clster{ind+1}: {i},{benchmark} finished.###')

	print(f'############clster{ind+1}: all finished##############')

	scheduler.sentinel_set(ind)
	return

##########################################


if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument('--cap', type=int, required=False, default=165)
	parser.add_argument('--alg', type=str, required=True)
	parser.add_argument('--count', type=int, required=False, default=0)
	parser.add_argument('--npb', type=str, required=False, default='')
	args = parser.parse_args()

	config.TDP = args.cap	
	out_file = f'spark_npb_{config.TDP}.csv'
	cap_file = config.RECORD_PATH.joinpath(f'spark_npb_{config.TDP}_caps_log')
	level_file = config.RECORD_PATH.joinpath(f'spark_npb_{config.TDP}_levels_log')
	est_file = config.RECORD_PATH.joinpath(f'spark_npb_{config.TDP}_est_log')
	duration_file_arr = [config.RECORD_PATH.joinpath(f'dyn_rapl_time_{i}') for i in range(config.CLUSTER_COUNT)]

	scheduler = DPS_supermaster(args.alg, cap_file = cap_file, level_file = level_file, est_file = est_file)

	# Start monitoring
	start_perf()
	start_rapl(outfile=config.TEMPT_PATH.joinpath('raplFile'))

	# Start dyn_rapl_supermaster thread
	supermaster_t = threading.Thread(target=scheduler.exec)
	supermaster_t.start()

	time.sleep(1)
	start_time = time.time()

	# Start threads
	
	BENCH_COUNTS = np.zeros(len(BENCHMARK_EQUAL)) if args.alg == 'equal' else np.zeros(len(BENCHMARK_HIBENCH))

	if args.alg == 'equal':
		cluster_t_arr = [threading.Thread(target=execute_cluster_equal, args=(i,args.count,duration_file_arr[i], scheduler)) for i in range(config.CLUSTER_COUNT)]
	elif args.npb and args.npb in config.NPB_CLASS:
		cluster_t_arr = [threading.Thread(target=execute_cluster_pairs, args=(i,args.npb,args.count,duration_file_arr[i], scheduler)) for i in range(config.CLUSTER_COUNT)]
	else:
		print(f'NPB benchmark {args.npb} does not exist.')
		for i in range(config.CLUSTER_COUNT):
			scheduler.sentinel_set(i)

	for t in cluster_t_arr:	t.start()
	for t in cluster_t_arr:	t.join()
	supermaster_t.join()

	end_time = time.time()


	# End monitoring
	end_monitoring(['perf','Rapl'])

	# Collect and generate reports
	collectPerfRecords()
	collectRaplRecords(config.TEMPT_PATH.joinpath('raplFile'))
	genPerfReport(outfile=config.RECORD_PATH.joinpath('perf_'+out_file), \
		start = start_time, end = end_time, start_ind=1, end_ind=10)
	genRaplReport(filename='raplFile',outfile=config.RECORD_PATH.joinpath(\
		f'rapl_'+out_file), start = start_time, end = end_time, \
		 start_ind=1, end_ind=10)