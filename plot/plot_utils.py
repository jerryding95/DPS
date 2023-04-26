import numpy as np
from pathlib import Path


def prepare_time_dict(directory):
	bench_arrs = [np.loadtxt(directory.joinpath(f'workload_time_{i}'), delimiter=',', usecols=[0], dtype=str) for i in range(2)]
	time_arrs = [np.loadtxt(directory.joinpath(f'workload_time_{i}'), delimiter=',', usecols=[1,2,3]) for i in range(2)]
	bench_arr = np.concatenate((bench_arrs[0],bench_arrs[1]))
	time_arr = np.concatenate((time_arrs[0],time_arrs[1]))

	data_dicts, data_dict = [{},{}], {}
	for i in range(2):
		for bench, time in zip(bench_arrs[i],time_arrs[i][:,2]):
			data_dicts[i][bench] = data_dicts[i].setdefault(bench, []) + [time]

	for bench, time in zip(bench_arr,time_arr[:,2]):
		data_dict[bench] = data_dict.setdefault(bench, []) + [time]

	return data_dicts, data_dict

def prepare_period_dict(directory):
	bench_arrs = [np.loadtxt(directory.joinpath(f'workload_time_{i}'), delimiter=',', usecols=[0], dtype=str) for i in range(2)]
	time_arrs = [np.loadtxt(directory.joinpath(f'workload_time_{i}'), delimiter=',', usecols=[1,2,3]) for i in range(2)]

	data_dicts = [{},{}]
	for i in range(2):
		for bench, time in zip(bench_arrs[i],time_arrs[i][:]):
			data_dicts[i][bench] = data_dicts[i].setdefault(bench, []) + [time]

	return data_dicts

def prepare_group_time_dict(directory, subdirs):
	group_dicts, group_dict = [{},{}], {}
	for dname in subdirs:
		data_dicts, data_dict = prepare_time_dict(directory.joinpath(dname))
		for i in range(2):
			for bench in data_dicts[i]:
				group_dicts[i][bench] = group_dicts[i].setdefault(bench, []) + data_dicts[i][bench]
		for bench in data_dict:
			group_dict[bench] = group_dict.setdefault(bench, []) + data_dict[bench]
	return group_dicts, group_dict

def prepare_pair_time_dict(directory):
	bench_arrs = [np.loadtxt(directory.joinpath(f'workload_time_{i}'), delimiter=',', usecols=[0], dtype=str) for i in range(2)]
	time_arrs = [np.loadtxt(directory.joinpath(f'workload_time_{i}'), delimiter=',', usecols=[1,2,3]) for i in range(2)]
	pair_time = time_arrs[1]

	data_dicts = [{},{}]
	for bench, time in zip(bench_arrs[0],time_arrs[0]):
		data_dicts[0][bench] = data_dicts[0].setdefault(bench, []) + [time]

	for bench in data_dicts[0]:
		data_dicts[1][bench] = \
			pair_time[( (pair_time[:,1] >= data_dicts[0][bench][0][0]) \
						& (pair_time[:,0] <= data_dicts[0][bench][-1][1]) ), 2]

	for bench in data_dicts[0]:
		data_dicts[0][bench] = np.array(data_dicts[0][bench])[:,2]

	return data_dicts

def prepare_rapl_dict(file_path):

	rapl_data = np.genfromtxt(file_path, skip_header=1, names=True, delimiter=',')
	length = rapl_data.shape[0]
	res = {}

	for name in rapl_data.dtype.names:

		if 'time' in name:
			res[name] = rapl_data[name]
			continue

		flag = name.split('_')[-1].isdigit()
		type_name = name.split('_')[1]
		worker_ind = int(name.split('_')[-1])+1 if flag else 1
		socket_ind = int(name[1])
		out_name = f'{type_name}_{worker_ind}_{socket_ind}'
		res[out_name] = rapl_data[name]

		# remove overflow values
		for i in range(1,length-1):
			if res[out_name][i] < 0: res[out_name][i] = (res[out_name][i-1]+res[out_name][i+1])/2

	return res

def prepare_power_arr(file_path, node_per_cluster, cluster_count):
	rapl_dict = prepare_rapl_dict(file_path)
	rapl_data = np.array(list(rapl_dict.items()), dtype=object)[:,1]
	rapl_data = np.array(rapl_data.tolist())
	rapl_data = rapl_data.reshape(node_per_cluster*cluster_count,5,rapl_data.shape[1])
	pkg_rapl_data = rapl_data[:,1:3]
	return rapl_data, pkg_rapl_data

def get_benchmark_period(rapl_data_dict, start_time, end_time, cluster_count, node_per_cluster):
	bench_periods_inds = np.empty((cluster_count*node_per_cluster,2),dtype=np.int32)
	for k,inds in enumerate(bench_periods_inds):
		name = 'time' if k == 0 else f'time_{k}'
		inds[0] = np.argmax(rapl_data_dict[name]>=start_time)
		inds[1] = np.argmax(rapl_data_dict[name]>=end_time) if rapl_data_dict[name][-1] >= end_time else len(rapl_data_dict[name])
	return bench_periods_inds

def get_avg_power(rapl_dict, pkg_rapl_data, cluster_ind, start_time, end_time, cluster_count, node_per_cluster):
	inds = get_benchmark_period(rapl_dict, start_time, end_time, cluster_count, node_per_cluster)
	return np.average([np.average(pkg_rapl_data[cluster_ind*4:cluster_ind*4+4,:,inds[j,0]:inds[j,1]]) for j in range(node_per_cluster*cluster_count)])

def prepare_power_baseline(directory, node_per_cluster, cluster_count):
	bench_arrs = [np.loadtxt(directory.joinpath(f'workload_time_{i}'), delimiter=',', usecols=[0], dtype=str) for i in range(2)]
	time_arrs = [np.loadtxt(directory.joinpath(f'workload_time_{i}'), delimiter=',', usecols=[1,2,3]) for i in range(2)]

	# rapl_data, pkg_rapl_data = prepare_power_arr(directory.joinpath('rapl_record.csv'), node_per_cluster, cluster_count)
	rapl_dict = prepare_rapl_dict(directory.joinpath('rapl_record.csv'))
	rapl_data = np.array(list(rapl_dict.items()), dtype=object)[:,1]
	rapl_data = np.array(rapl_data.tolist())
	print(rapl_data.shape)
	rapl_data = rapl_data.reshape(node_per_cluster*cluster_count,5,rapl_data.shape[1])
	pkg_rapl_data = rapl_data[:,1:3]

	power_dict = {}
	for i in range(2):
		for bench, time in zip(bench_arrs[i],time_arrs[i]):
			avg_power = get_avg_power(rapl_dict, pkg_rapl_data, i, time[0], time[1], cluster_count, node_per_cluster-1)
			# bench_periods_inds = get_benchmark_period(rapl_dict, time[0], time[1], cluster_count, node_per_cluster)
			# avg_power = np.average(\
			# 	[np.average(pkg_rapl_data[4*i:4+4*i,:,bench_periods_inds[j,0]:bench_periods_inds[j,1]]) \
			# 	for j in range(node_per_cluster*cluster_count)])
			power_dict[bench] = power_dict.setdefault(bench, []) + [avg_power]
	for bench in power_dict:
		power_dict[bench] = np.average(power_dict[bench])

	return power_dict

def get_pair_time(directory):
	data_dicts = prepare_period_dict(directory)
	# print(data_dicts[0])
	pair_time = np.array(data_dicts[1][list(data_dicts[1].keys())[0]])
	# print(pair_time)
	spark_data = data_dicts[0]
	pair_data = {}
	for bench in spark_data:
		spark_data[bench] = np.array(spark_data[bench])
		# print(spark_data[bench])
		pair_data[bench] = pair_time[((pair_time[:,1] >= spark_data[bench][0,0]) & (pair_time[:,0] <= spark_data[bench][-1,1])), :]

	# pair_data = {bench: pair_time[((pair_time[:][1] >= data_dicts[0][bench][0][0]) & (pair_time[:][0] <= data_dicts[0][bench][-1][1])), :] \
	# 	for bench in data_dicts[0]}
	return spark_data, pair_data


def prepare_pair_power(directory,node_per_cluster,cluster_count):

	spark_data, pair_data = get_pair_time(directory)
	rapl_dict = prepare_rapl_dict(directory.joinpath(f'rapl_record.csv'))
	rapl_data = np.array(list(rapl_dict.items()), dtype=object)[:,1]
	rapl_data = np.array(rapl_data.tolist())
	rapl_data = rapl_data.reshape(node_per_cluster*cluster_count,5,rapl_data.shape[1])
	pkg_rapl_data = rapl_data[:,1:3]

	avg_power = {}

	for bench in spark_data:
		avg_power[bench] = [np.average([get_avg_power(rapl_dict, pkg_rapl_data, 0, l[0], l[1],node_per_cluster,cluster_count) for l in spark_data[bench]]),
							np.average([get_avg_power(rapl_dict, pkg_rapl_data, 1, l[0], l[1],node_per_cluster,cluster_count) for l in pair_data[bench]])]
	return avg_power


def prepare_group_power(parent_directory, subdirs,node_per_cluster,cluster_count):
	group_avg_power = {}
	for d in subdirs:
		directory = parent_directory.joinpath(d)
		group_avg_power[d] = prepare_pair_power(directory,node_per_cluster,cluster_count)
	return group_avg_power

def get_fairness(group_avg_power, baseline):
	re = {}
	for bench in group_avg_power:
		re[bench] = {}
		for b in group_avg_power[bench]:
			re[bench][b] = 1-abs(group_avg_power[bench][b][0]/baseline[b]-group_avg_power[bench][b][1]/baseline[bench])
	return re

def fairness_dict_to_arr(fairness):
	return np.array([list(d.values()) for d in fairness.values()]).ravel()










