import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats
from plot_utils import *


BENCHMARKS_HIGH = ['kmeans', 'lda', 'linear', 'lr', 'bayes', 'rf', 'gmm']
BASELINE_PATH = Path('../records/const/')
RECORD_PATH = Path('../records/high_util/')
colors = ['#D5BA82','#A1D0C7']
labels = ['DPS','SLURM']
names = ['Kmeans', 'LDA', 'Linear', 'LR', 'Bayes', 'RF', 'GMM', 'Hmean']

if __name__ == '__main__':


	_, baseline_dict = prepare_time_dict(BASELINE_PATH)
	data_dicts = prepare_pair_time_dict(RECORD_PATH.joinpath('dps'))
	slurm_dicts = prepare_pair_time_dict(RECORD_PATH.joinpath('slurm'))

	mean_arr_arrs = np.zeros((2, 2, len(BENCHMARKS_HIGH)))
	mean_arrs = np.zeros((2, 2, len(BENCHMARKS_HIGH)+1))

	for i, dicts in enumerate(zip(data_dicts,slurm_dicts)):
		mean_arr_arrs[i,0] = [stats.hmean(baseline_dict[bench])/stats.hmean(data_dicts[0][bench]) for bench in BENCHMARKS_HIGH]
		mean_arr_arrs[i,1] = [stats.hmean(baseline_dict['gmm'])/stats.hmean(data_dicts[1][bench]) for bench in BENCHMARKS_HIGH]

	for i in range(2):
		mean_arrs[i,0,:-1] = mean_arr_arrs[i,0]
		mean_arrs[i,1,:-1] = [stats.hmean([mean_arr_arrs[i,0,j],mean_arr_arrs[i,1,j]]) for j in range((len(BENCHMARKS_HIGH)))]
		mean_arrs[i,0,-1] = stats.hmean(mean_arrs[i,0,:-1])
		mean_arrs[i,1,-1] = stats.hmean(mean_arrs[i,1,:-1])



	x = np.arange(len(BENCHMARKS_HIGH)+1)
	width = 0.3
	fig, axs = plt.subplots(2,figsize=(5,2.5)) 

	for k in range(2):
		for i in range(2):
			axs[k].bar(x + width * (i - .5), mean_arrs[k,i]-1, width = width, label = labels[i], color=colors[i]) 
			axs[k].bar(x + width * (i - .5), mean_arrs[k,i]-1, width = width, label = labels[i], color=colors[i]) 
		axs[k].set_xticks(x, names)
		axs[k].grid(axis = 'y',which='major')


	axs[0].set_xlabel('(a) Application\'s performance when paired with GMM')
	axs[1].set_xlabel('(b) Hmean performance of the application and its paired GMM')
	axs[0].set_ylim([-.15, .15])
	axs[1].set_ylim([-.1,.1])

	handles, labels = axs[0].get_legend_handles_labels()
	fig.legend(handles=handles,bbox_to_anchor=(.58, .9, 0, 0), loc='lower center', ncol = 2, frameon = False, handlelength = 8.0, columnspacing = 6)
	fig.supylabel('Speedup normalized to\nperformance under Constant 110W cap', horizontalalignment='center', fontsize=8)
	plt.subplots_adjust(top = .86, bottom = 0, right = 1, left = 0.15, hspace=0.6)
	plt.show()
	# plt.savefig('high_util_speedup.pdf', bbox_inches='tight', dpi=100)






