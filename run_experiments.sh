#!/bin/bash

spark_low_bench=("wordcount" "sort" "terasort" "repartition")
spark_high_bench=("kmeans" "lda" "lr" "linear" "bayes" "rf" "gmm")
npb_bench=("bt" "cg" "ep" "ft" "is" "lu" "mg" "sp")

mkdir records

# Run Constant Allocation
python3 exp.py --cap 110 --pms const --count 10 --record records/const

# Run Low utility experiment group
mkdir records/low_util
mkdir records/low_util/slurm
mkdir records/low_util/dps
mkdir records/low_util/oracle
for b in ${spark_low_bench[@]}
do
	python3 exp.py --cap 110 --pms dps --count 10 --pair_bench ${b} --record records/low_util/dps/${b}
	python3 exp.py --cap 110 --pms slurm --count 10 --pair_bench ${b} --record records/low_util/slurm/${b}
	python3 exp.py --pms oracle --count 10 --pair_bench ${b} --record records/low_util/oracle/${b}
done

# Run High utility experiment group
mkdir records/high_util
mkdir records/high_util/slurm
mkdir records/high_util/dps
for b in ${spark_high_bench[@]}
do
	python3 exp.py --cap 110 --pms dps --count 10 --pair_bench gmm --record records/low_util/dps/${b}
	python3 exp.py --cap 110 --pms slurm --count 10 --pair_bench gmm --record records/low_util/slurm/${b}
done

# Run Spark NPB experiment group
mkdir records/spark_npb
mkdir records/spark_npb/slurm
mkdir records/spark_npb/dps
for b in ${npb_bench[@]}
do
	python3 exp.py --cap 110 --pms dps --count 10 --pair_bench ${b} --record records/low_util/dps/${b}
	python3 exp.py --cap 110 --pms slurm --count 10 --pair_bench ${b} --record records/low_util/slurm/${b}
done