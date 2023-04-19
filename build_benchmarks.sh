#!/bin/bash
num_clusters=2

cmd="cwd=$(pwd)
cd ~/HiBench
mvn -Psparkbench -Dmodules -Pmicro clean package
mvn -Psparkbench -Dmodules -Pml clean package
cd $cwd
/home/cc/hadoop/bin/hdfs namenode -format
/home/cc/hadoop/sbin/start-dfs.sh
/home/cc/hadoop/bin/hdfs dfs -mkdir -p /user/cc/
/home/cc/hadoop/sbin/start-yarn.sh
/home/cc/spark/sbin/start-master.sh
/home/cc/spark/sbin/start-slaves.sh spark://master:7077"

# Build Hibench workloads, start hadoop and spark
for i in $(seq 1 $num_clusters)
do
    ssh master${i} $cmd
done

micro_workloads=("wordcount" "sort" "terasort" "repartition")
ml_workloads=("kmeans" "lda" "lr" "linear" "bayes" "rf" "gmm")

for i in $(seq 1 $num_clusters)
do
	# Prepare Spark Workloads
	ssh master${i} "sed -i '3s/.*/hibench.scale.profile                large/' conf/hibench.conf"
	for w in ${micro_workloads[@]}
	do
		ssh master${i} "/home/cc/HiBench/bin/workload/micro/${w}/prepare.sh"
	done
	ssh master${i} "sed -i '3s/.*/hibench.scale.profile                bigdata/' conf/hibench.conf"
	for w in ${ml_workloads[@]}
	do
		ssh master${i} "/home/cc/HiBench/bin/workload/ml/${w}/prepare.sh"
	done

	# Build NPB Workloads
	ssh master${i} "cd /home/cc/NPB3.4.2/NPB3.4-MPI/; build all"
done
	
	

