#!/bin/bash

hwd=$HOME
num_clusters=$NUM_CLUSTERS
num_nodes=$(cat conf/clusterIPs | wc -l)
num_clients=$(($num_nodes-1))

eval `ssh-agent -s`
ssh-add ${hwd}/.ssh/${KEY}


for i in $(seq 1 $num_clients)
do
	# Build NPB Workloads
	ssh slave${i} "cd ${hwd}/NPB3.4.2/NPB3.4-MPI/; make suite"
done
	
	

