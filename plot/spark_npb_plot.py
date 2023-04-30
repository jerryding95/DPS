import numpy as np
import sys
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats
from plot_utils import *

BENCHMARKS_HIBENCH = ['kmeans', 'lda', 'linear', 'lr', 'bayes', 'rf', 'gmm']
BENCHMARKS_NPB = ['bt', 'cg', 'ep', 'ft', 'is', 'lu', 'mg', 'sp']
colors = ['#D5BA82','#A1D0C7']
BASELINE_PATH = Path('../records/const/')
RECORD_PATH = Path('../records/spark_npb/')


if __name__ == '__main__':

	_, baseline_dict = prepare_time_dict(BASELINE_PATH)
	dps_dicts_arr = [prepare_pair_time_dict(RECORD_PATH.joinpath(f'dps/{b}')) for b in BENCHMARKS_NPB]
	slurm_dicts_arr = [prepare_pair_time_dict(RECORD_PATH.joinpath(f'slurm/{b}')) for b in BENCHMARKS_NPB]

	dps_avg_arr = np.zeros((len(BENCHMARKS_NPB), len(BENCHMARKS_HIBENCH)))
	slurm_avg_arr = np.zeros((len(BENCHMARKS_NPB), len(BENCHMARKS_HIBENCH)))

	for i,npb_bench in enumerate(BENCHMARKS_NPB):
		for j, spark_bench in enumerate(BENCHMARKS_HIBENCH):
			dps_avg_arr[i][j] = stats.hmean(\
								[stats.hmean(dps_dicts_arr[i][0][spark_bench]), \
								stats.hmean(dps_dicts_arr[i][1][spark_bench])])
			slurm_avg_arr[i][j] = stats.hmean(\
								[stats.hmean(slurm_dicts_arr[i][0][spark_bench]), \
								stats.hmean(slurm_dicts_arr[i][1][spark_bench])])

	fig, axs = plt.subplots(2, figsize = (5,2.5))
	width = .3
	x = np.arange(len(BENCHMARKS_HIBENCH)+1)
	axs[0].bar(x - width/2, np.append(stats.hmean(dps_avg_arr)-1, [stats.hmean(dps_avg_arr.ravel())-1]), width = width, label = 'DPS', color=colors[0])
	axs[0].bar(x + width/2, np.append(stats.hmean(slurm_avg_arr)-1, [stats.hmean(slurm_avg_arr.ravel())-1]), width = width, label = 'SLURM', color=colors[1])
	axs[0].set_xticks(x, BENCHMARKS_HIBENCH+['Hmean'])
	

	x = np.arange(len(BENCHMARKS_NPB)+1)
	axs[1].bar(x - width/2, np.append(stats.hmean(dps_avg_arr.T)-1, [stats.hmean(dps_avg_arr.ravel())-1]), width = width, label = 'DPS', color=colors[0])
	axs[1].bar(x + width/2, np.append(stats.hmean(slurm_avg_arr.T)-1, [stats.hmean(slurm_avg_arr.ravel())-1]), width = width, label = 'SLURM', color=colors[1])
	axs[1].set_xticks(x, BENCHMARKS_NPB+['Hmean'])

	axs[0].set_xlabel('(a) Hmean of paired applications across Spark applications')
	axs[1].set_xlabel('(b) Hmean of paired applications across NPB applications')
	axs[0].grid(axis = 'y',which='major')
	axs[1].grid(axis = 'y',which='major')
	handles, labels = axs[0].get_legend_handles_labels()
	fig.legend(handles=handles,bbox_to_anchor=(.58, .9, 0, 0), loc='lower center', ncol = 2, frameon = False, handlelength = 8.0, columnspacing = 6)
	fig.supylabel('Speedup normalized to\nperformance under Constant 110W cap', horizontalalignment='center', fontsize=8)
	plt.subplots_adjust(top = .86, bottom = 0, right = 1, left = 0.15, hspace=0.6)
	plt.show()
	# plt.savefig('spark_npb_speedup.pdf', bbox_inches='tight', dpi=100)




	

