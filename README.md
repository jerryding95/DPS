# DPS

Project Description
----------------------------------------
This artifact is part of the paper DPS: Adaptive Power Management for Overprovisioned Systems.

Dependency
----------------------------------------
The experiments in the paper is conducted with packages in the following versions:
Ubuntu 18.04
Python 3.6
Java OpenJDK 8u362-b9
Hadoop 2.7.7
Spark 2.4.8
HiBench 7.1
NPB 3.4.2

However we require a Python version newer than 3.8 to reproduce the experiment results, as we
have packed DPS into a Python package which needs Python in newer version to build.

Setting up the cluster
----------------------------------------
Before setting up the cluster, the user needs copy the public key file into the control node's 
`$HOME/.ssh/` directory, and enter correct information in the `conf/clusterIPs` file
and `src/config.py` file accordingly. All nodes need to use the same private and public keys. Enter
the home directory, public key file name, and number of clusters in `setup_cluster.sh`

Execute the following commands to setup connections, install packages and configure packages.
Users can install the above packages independently. The setup_cluster.sh script also includes 
installing and configuring the above packages. 

./setup_cluster.sh <args>

Use args to declare packages to install, which includes java, hadoop, spark, hibench, npb. For
example, execute the following commands to setup everything on an empty node.

./setup_cluster.sh java hadoop spark hibench npb

Initialize Hadoop, Spark and Spark workloads
----------------------------------------
SSH into the two master nodes. Then execute the following commands to build all benchmark 
workloads used in the paper.

$HOME/DPS/initialize_hibench_hadoop_spark.sh


Running Experiments
----------------------------------------
Execute the following commands to run all experiments in the paper

./run_benchmarks.sh

Instead, users can execute the folowing commands to run smaller groups of experiment

python3 exp.py <--arg arg>

The arguments description is as followed:
--cap			the power cap per socket
--pms			the power management system, one of const, slurm, dps, oracle.
				If the pms is const, all mid-power, high-power, and NPB workloads will be executed.
				Otherwise all mid-power and high-power workloads will be executed while paiered with
				another workload specified by --pair_bench argument.
--count			the repetition for each workload
--pair_bench	the one workload pairing with all mid-power and high-power workloads
--record		name of the output results directory

Additional Notes:  

Benchmarks
----------------------------------------

Directory Structure  
----------------------------------------  
