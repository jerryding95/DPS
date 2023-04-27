#!/bin/bash

repeat=10
sleeptime=60
spark_low_bench=("sort" "terasort" "repartition" "wordcount")
spark_high_bench=("kmeans" "lda" "lr" "linear" "bayes" "rf" "gmm")
npb_bench=("bt" "cg" "ep" "ft" "is" "lu" "mg" "sp")

mkdir records

# Run Constant Allocation
python3 exp.py --cap 110 --pms const --count ${repeat} --record records/const
sleep 60

# Run Constant Allocation with TDP as cap, for plotting fairness
python3 exp.py --cap 165 --pms const --count ${repeat} --record records/unlimited
sleep 60

# Run Low utility experiment group
mkdir records/low_util
mkdir records/low_util/slurm
mkdir records/low_util/dps
mkdir records/low_util/oracle
for b in ${spark_low_bench[@]}
do
	python3 exp.py --cap 110 --pms dps --count ${repeat} --pair_bench ${b} --record records/low_util/dps/${b}
	sleep ${sleeptime}
	python3 exp.py --cap 110 --pms slurm --count ${repeat} --pair_bench ${b} --record records/low_util/slurm/${b}
	sleep ${sleeptime}
	python3 exp.py --pms oracle --count ${repeat} --pair_bench ${b} --record records/low_util/oracle/${b}
	sleep ${sleeptime}
done

# Run High utility experiment group
mkdir records/high_util
mkdir records/high_util/slurm
mkdir records/high_util/dps

python3 exp.py --cap 110 --pms dps --count ${repeat} --pair_bench gmm --record records/high_util/dps
sleep ${sleeptime}
python3 exp.py --cap 110 --pms slurm --count ${repeat} --pair_bench gmm --record records/high_util/slurm
sleep ${sleeptime}


# Run Spark NPB experiment group
mkdir records/spark_npb
mkdir records/spark_npb/slurm
mkdir records/spark_npb/dps
for b in ${npb_bench[@]}
do
	# python3 exp.py --cap 110 --pms dps --count ${repeat} --pair_bench ${b} --record records/spark_npb/dps/${b}
	# sleep ${sleeptime}
	python3 exp.py --cap 110 --pms slurm --count ${repeat} --pair_bench ${b} --record records/spark_npb/slurm/${b}
	sleep ${sleeptime}
done
