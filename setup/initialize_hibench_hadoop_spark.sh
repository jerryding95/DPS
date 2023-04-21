#!/bin/bash

sudo apt install --assume-yes maven python2;
cwd=$(pwd);
cd $HOME/HiBench;
mvn -Psparkbench -Dmodules -Pmicro clean package;
mvn -Psparkbench -Dmodules -Pml clean package;
cd $cwd;

# Setup Hadoop
/home/cc/hadoop/bin/hdfs namenode -format
/home/cc/hadoop/sbin/start-dfs.sh
/home/cc/hadoop/bin/hdfs dfs -mkdir -p /user/cc/
/home/cc/hadoop/sbin/start-yarn.sh

# Setup Spark
/home/cc/spark/sbin/start-master.sh
/home/cc/spark/sbin/start-slaves.sh spark://master:7077

micro_workloads=("wordcount" "sort" "terasort" "repartition")
ml_workloads=("kmeans" "lda" "lr" "linear" "bayes" "rf" "gmm")

sed -i '3s/.*/hibench.scale.profile                large/' \$HOME/HiBench/conf/hibench.conf
for w in ${micro_workloads[@]}
do
	$HOME/HiBench/bin/workloads/micro/${w}/prepare/prepare.sh
done
sed -i '3s/.*/hibench.scale.profile                bigdata/' \$HOME/HiBench/conf/hibench.conf
for w in ${ml_workloads[@]}
do
	$HOME/HiBench/bin/workloads/ml/${w}/prepare/prepare.sh
done