#!/bin/bash

declare -A prefixes
prefixes=([bayes]="ml" [gbt]="ml" ["kmeans"]="ml" [lda]="ml" [linear]="ml" \
	[lr]="ml" [pca]="ml" [rf]="ml" [svd]="ml" [svm]="ml" [als]="ml"\
	[wordcount]="micro" [terasort]="micro" [dfsioe]="micro"\
	 [repartition]="micro" [sleep]="micro" [sort]="micro")

benchmark=$1
parallelism=$2
cores_per_executor=8
executor_count=$((parallelism / cores_per_executor))
type=${prefixes[$benchmark]}

# echo sed -i "5s/.*/hibench.default.map.parallelism         $parallelism/" /home/cc/HiBench/conf/hibench.conf
sed -i "10s/.*/hibench.yarn.executor.num     $executor_count/" /home/cc/HiBench/conf/spark.conf

start_time=$(date +%s)
/home/cc/HiBench/bin/workloads/$type/$benchmark/spark/run.sh
end_time=$(date +%s)
duraion=$((end_time - start_time))
echo $start_time $end_time $duraion