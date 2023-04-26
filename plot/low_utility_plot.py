import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats
from plot_utils import *


BENCHMARKS_HIGH = ['kmeans', 'lda', 'linear', 'lr', 'bayes', 'rf', 'gmm']
BENCHMARKS_LOW = ['wordcount', 'sort', 'terasort', 'repartition']
BASELINE_PATH = Path('../records/const/')
RECORD_PATH = Path('../records/low_util/')
labels = ['DPS','Oracle','SLURM']
colors = ['#D5BA82','#B36A6F','#A1D0C7']
names = ['Kmeans', 'LDA', 'Linear', 'LR', 'Bayes', 'RF', 'GMM', 'Hmean']

if __name__ == '__main__':

	_, baseline_dict = prepare_time_dict(BASELINE_PATH)
	_, data_dict = prepare_group_time_dict(RECORD_PATH.joinpath('dps'), BENCHMARKS_LOW)
	_, oracle_dict = prepare_group_time_dict(RECORD_PATH.joinpath('oracle'), BENCHMARKS_LOW)
	_, slurm_dict = prepare_group_time_dict(RECORD_PATH.joinpath('slurm'), BENCHMARKS_LOW)
	
	dict_arr = [baseline_dict, data_dict, oracle_dict, slurm_dict]

	mean_arr_arrs = [[stats.hmean(baseline_dict[bench])/stats.hmean(d[bench]) for bench in BENCHMARKS_HIGH] for d in dict_arr[1:]]
	for i in range(len(mean_arr_arrs)):
		mean_arr_arrs[i].append(stats.hmean(mean_arr_arrs[i]))

	x = np.arange(len(BENCHMARKS_HIGH)+1)
	width = 0.2

	fig, ax = plt.subplots(figsize=(13, 1), sharex=True, sharey=True)
	bars = [ax.bar(x + width * (i - 1), np.array(mean_arr_arrs[i])-1, width = width, label = labels[i], color = colors[i]) for i in range(len(mean_arr_arrs))]

	ax.grid(axis = 'y',which='major')
	ax.set_ylim([-.05, .2])
	ax.set_xticks(x,names)

	fig.supylabel('Speedup normalized to\nperformance under\nconstant 110W cap', horizontalalignment='center', fontsize = 8)
	handles, labels = ax.get_legend_handles_labels()
	fig.legend(handles=handles,labels=labels,bbox_to_anchor=(.5, 1, 0, 0), loc='lower center', ncol = 4, frameon = False, handlelength = 10.0, columnspacing = 8.0)
	plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0.075)


	plt.show()
	# plt.savefig('low_util_speedup.pdf', bbox_inches='tight', dpi=100)






