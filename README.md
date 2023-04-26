# DPS - Dynamic Power Scheduler

Project Description
----------------------------------------
This artifact is part of the paper DPS: Adaptive Power Management for Overprovisioned Systems.

Dependency
----------------------------------------
The experiments in the paper is conducted with packages in the following versions: <br />
Ubuntu 18.04 <br />
Python 3.6 <br />
Java OpenJDK 8u362-b9 <br />
Hadoop 2.7.7 <br />
Spark 2.4.8 <br />
HiBench 7.1 <br />
NPB 3.4.2 <br />

However we require a Python version newer than 3.8 to reproduce the experiment results, as we
have packed DPS into a Python package which needs Python in a newer version to build.

Setting up the cluster
----------------------------------------
Before setting up the cluster, the user needs copy the public key file into the control node's `$HOME/.ssh/` directory, and enter ip-addresses in the `conf/clusterIPs` file and `src/config.py` file accordingly. All client nodes need to use the same private and public keys. The control node is named as `supermaster` and the client nodes are names as `slave${i}`. The master nodes are laied out as the last two slave nodes. In the default `conf/clusterIPs` file, for example, there are 10 client nodes separated into 2 sub-clusters. For cluster1, slave9 is the master node and slave1-4 are the worker nodes. For cluster2, slave10 is the master node and slave 5-8 are the worker nodes. Besides, the user also needs to enter the  public key file name, and number of sub-clusters in `setup/setup_cluster.sh`

Execute the following commands to download the repository and locate the files in which configuration needs to be edited.
```
git clone https://github.com/jerryding95/DPS.git
cd DPS
# Make modifications in setup/setupcluster.sh, conf/clusterIPs, and src/config.py accordingly
```

Then execute the following command to install packages and configure packages. 
```
git clone https://github.com/jerryding95/DPS.git
cd DPS
./setup_cluster.sh <args>
```

Users can install the required packages independently, but the setup_cluster.sh script also includes installing and configuring the above packages. Use args to declare packages to install, which includes java, hadoop, spark, hibench, npb. For example, instead of the last line as shown above, execute the following commands to setup and install java, hadoop, spark, HiBench and NPB workloads on the empty cluster.
```
./setup_cluster.sh java hadoop spark hibench npb
```

Initialize Hadoop, Spark and HiBench workloads
----------------------------------------
Once the above script completes, SSH into the two master nodes ad execute the following command to start the Hadoop and Spark processes, and build all required Spark workloads in HiBench.
```
$HOME/DPS/initialize_hibench_hadoop_spark.sh
```

Running Experiments
----------------------------------------
Execute the following commands to run all experiments in the paper
```
./run_benchmarks.sh
```
Instead, users can execute the folowing commands to run smaller groups of experiment
```
python3 exp.py <--arg arg>
```
The arguments description is as followed: <br />
- --cap			
	- the power cap per socket <br />
- --pms			
	- the power management system, one of const, slurm, dps, oracle. If the pms is const, all mid-power, high-power, and NPB workloads will be executed. Otherwise all mid-power and high-power workloads will be executed while paiered with another workload specified by --pair_bench argument. 
- --count		
	- the repetition for each workload <br />
- --pair_bench		
	- the one workload pairing with all mid-power and high-power workloads <br />
- --record		
	- name of the output results directory <br />


Benchmarks
----------------------------------------

Directory Structure  
----------------------------------------  
