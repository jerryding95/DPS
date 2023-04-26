import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from plot_utils import *

node_per_cluster = 4
cluster_count = 2
BENCHMARKS_SPARK = ['kmeans', 'lda', 'linear', 'lr', 'rf', 'bayes', 'gmm']
BENCHMARKS_NPB = ['bt', 'cg', 'ep', 'ft', 'is', 'lu', 'mg', 'sp']
BASELINE_PATH = Path('../records/unlimited/')
HIGH_UTIL_PATH = Path('../records/high_util')
SPARK_NPB_PATH = Path('../records/spark_npb')
colors = ['#D5BA82','#A1D0C7']


if __name__ == '__main__':

############################################################################################################################
# Get baseline power
	
	baseline_power_dict = prepare_power_baseline(BASELINE_PATH, node_per_cluster+1, cluster_count)


############################################################################################################################

# SPARK_NPB Group data

	slurm_spark_npb_avg_power = prepare_group_power(SPARK_NPB_PATH.joinpath('slurm'), BENCHMARKS_NPB,node_per_cluster+1,cluster_count)
	dps_spark_npb_avg_power = prepare_group_power(SPARK_NPB_PATH.joinpath('dps'), BENCHMARKS_NPB,node_per_cluster+1,cluster_count)

	slurm_spark_npb_fairness = get_fairness(slurm_spark_npb_avg_power, baseline_power_dict)
	dps_spark_npb_fairness = get_fairness(dps_spark_npb_avg_power, baseline_power_dict)


############################################################################################################################

# High util Group data

	slurm_high_util_avg_power = {'gmm': prepare_pair_power(HIGH_UTIL_PATH.joinpath('slurm'),node_per_cluster+1,cluster_count)}
	dps_high_util_avg_power = {'gmm': prepare_pair_power(HIGH_UTIL_PATH.joinpath('dps'),node_per_cluster+1,cluster_count)}

	slurm_high_util_fairness = get_fairness(slurm_high_util_avg_power, baseline_power_dict)
	dps_high_util_fairness = get_fairness(dps_high_util_avg_power, baseline_power_dict)


############################################################################################################################

	dps_high_util_fairness_arr = fairness_dict_to_arr(dps_high_util_fairness)
	dps_spark_npb_fairness_arr = fairness_dict_to_arr(dps_spark_npb_fairness)
	slurm_high_util_fairness_arr = fairness_dict_to_arr(slurm_high_util_fairness)
	slurm_spark_npb_fairness_arr = fairness_dict_to_arr(slurm_spark_npb_fairness)

	# dps_high_util_fairness_arr = dps_high_util_fairness_arr[~np.isnan(dps_high_util_fairness_arr)]
	# dps_spark_npb_fairness_arr = dps_spark_npb_fairness_arr[~np.isnan(dps_spark_npb_fairness_arr)]
	# slurm_high_util_fairness_arr = slurm_high_util_fairness_arr[~np.isnan(slurm_high_util_fairness_arr)]
	# slurm_spark_npb_fairness_arr = slurm_spark_npb_fairness_arr[~np.isnan(slurm_spark_npb_fairness_arr)]

	colors = ['#D5BA82','#A1D0C7']
	fig, ax = plt.subplots(figsize = (5,2))
	x = np.arange(2)
	width = .2

	bplot1 = ax.boxplot([dps_high_util_fairness_arr, \
						dps_spark_npb_fairness_arr], \
						positions = x-width, patch_artist=True)
	bplot2 = ax.boxplot([slurm_high_util_fairness_arr, \
						slurm_spark_npb_fairness_arr], \
						positions = x+width, patch_artist=True)

	for patch in bplot1['boxes']:
		patch.set_facecolor(colors[0])
	for patch in bplot2['boxes']:
		patch.set_facecolor(colors[1])
	fig.legend([bplot1["boxes"][0], bplot2["boxes"][0]], ['DPS', 'SLURM'],bbox_to_anchor=(.53, .9, 0, 0), loc='lower center', ncol = 2, frameon = False, handlelength = 8.0, columnspacing = 4)
	ax.set_xticks(x,['Spark High Utility','Spark NPB'])
	ax.set_ylabel('Fairness')
	plt.show()
	# plt.savefig('/Users/jerryding/dyn_rapl_figures/figure8.pdf', bbox_inches='tight', dpi=100)



