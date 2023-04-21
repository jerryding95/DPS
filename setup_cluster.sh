#!/bin/bash

key="skylakeWorker.pem"
num_clusters=2

hwd=$HOME
export KEY=${key}
export NUM_CLUSTERS=${num_clusters}
echo "export KEY=${key}" >> ${hwd}/.bashrc
echo "export NUM_CLUSTERS=${num_clusters}" >> ${hwd}/.bashrc

num_nodes=$(cat conf/clusterIPs | wc -l)
num_clients=$(($num_nodes-1))
num_workers=$((num_clients/num_clusters-1))


function install_java {
    # sudo apt install openjdk-8-jdk
    # echo "export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64/" >> ${hwd}/.bashrc
    for i in $(seq 1 $num_clients)
    do
        ssh slave${i} "sudo apt update;
        sudo apt install openjdk-8-jdk;
        echo \"export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64/\" >> ${hwd}/.bashrc"
    done
}

function install_hadoop {
    wget "https://archive.apache.org/dist/hadoop/common/hadoop-2.7.7/hadoop-2.7.7.tar.gz"
    tar -xf hadoop-2.7.7.tar.gz 
    mv hadoop-2.7.7 ${hwd}/hadoop
    cp conf/hadoop/* ${hwd}/hadoop/etc/hadoop/
    rm ${hwd}/hadoop/etc/hadoop/slaves
    for w in $(seq 1 $num_workers);
    do
        echo slave${w} >> ${hwd}/hadoop/etc/hadoop/slaves
    done
    for i in $(seq 1 $num_clients)
    do
        scp -r ${hwd}/hadoop slave${i}:${hwd}/
        ssh slave${i} \
        "echo \"export HADOOP_HOME=${hwd}/hadoop/\" >> ${hwd}/.bashrc;
        echo \"export PATH=\\\$PATH:${hwd}/hadoop/bin/\" >> ${hwd}/.bashrc"
    done
}

function install_spark {
    wget "https://archive.apache.org/dist/spark/spark-2.4.8/spark-2.4.8-bin-hadoop2.7.tgz"
    tar -xf spark-2.4.8-bin-hadoop2.7.tgz
    mv spark-2.4.8-bin-hadoop2.7 ${hwd}/spark
    cp conf/spark/* ${hwd}/spark/conf/
    rm ${hwd}/spark/conf/slaves
    for w in $(seq 1 $num_workers);
    do
        echo slave${w} >> ${hwd}/spark/conf/slaves
    done
    for i in $(seq 1 $num_clients)
    do
        scp -r ${hwd}/spark slave${i}:${hwd}/
        ssh slave${i} \
        "echo \"export SPARK_HOME=${hwd}/spark/\" >> ${hwd}/.bashrc;
        echo \"export PATH=\\\$PATH:${hwd}/spark/bin/\" >> ${hwd}/.bashrc"
    done
}

function install_hibench {
    lines=$(tail -$num_clusters conf/clusterIPs)
    SAVEIFS=$IFS
    IFS=$'\n'
    lines=($lines)
    IFS=$SAVEIFS

    for i in $(seq 1 $num_clusters)
    do
        ssh master${i} \
        "git clone --branch HiBench-7.1-22-g827c9f69 https://github.com/Intel-bigdata/HiBench.git;
        mv HiBench ${hwd}/HiBench"

        line=(${lines[$((i-1))]})
        masterip=${line[0]}

        start=$((2+${num_workers}*$((i-1))))
        end=$((1+${num_workers}*${i}))
        worker_lines=$(sed -n "$start,$end p" conf/clusterIPs)
        SAVEIFS=$IFS
        IFS=$'\n'
        worker_lines=($worker_lines)
        IFS=$SAVEIFS
        workerips=""
        for (( j=0; j<${#worker_lines[@]}; j++ ))
        do
            line=(${worker_lines[$j]})
            workerips="${workerips} ${line[0]}"
        done

        # masterip=${$(sed -n "1,1p" conf/clusterIPs_${i})[1]}
        # workerips=""
        # for j in (seq 1 ${num_workers})
        # do
        #     workerips="${workerips} ${$(sed -n "2,$((num_workers+1))p" conf/clusterIPs_${i})[$((2*j-1))]}"
        # done

        scp conf/HiBench/* master${i}:${hwd}/HiBench/conf/
        ssh master${i} \
        "echo spark.yarn.preserve.staging.files=false >> ${hwd}/spark/conf/spark-defaults.conf;
        sed -i '/hibench.masters.hostnames/ c\hibench.masters.hostnames    ${masterip}' ${hwd}/HiBench/conf/hibench.conf;
        sed -i '/hibench.slaves.hostnames/ c\hibench.slaves.hostnames     ${workerips}' ${hwd}/HiBench/conf/hibench.conf;"
    done
}

function install_npb {
    for i in $(seq 1 $num_clients)
    do
        ssh slave${i} \
        "wget \"https://www.nas.nasa.gov/assets/npb/NPB3.4.2.tar.gz\";
        tar -xf NPB3.4.2.tar.gz;
        mv NPB3.4.2 ${hwd}/;
        sudo apt install gfortran libopenmpi-dev;
        for i in \$(seq 1 $num_workers);
        do echo \"slave\${i} slots=48 max_slots=96\";
        done"
        scp conf/NPB/* slave${i}:${hwd}/NPB3.4.2/NPB3.4-MPI/config/

        # Compile NPB Workloads
        for i in $(seq 1 $num_clients)
        do
            ssh slave${i} "cd ${hwd}/NPB3.4.2/NPB3.4-MPI/; make suite"
        done
    done
}



################################################################################
######################## Establish Cluster Connections #########################
eval `ssh-agent -s`
ssh-add ${hwd}/.ssh/${key}

echo 'eval `ssh-agent -s`' >> ${hwd}/.bashrc
echo "ssh-add ${hwd}/.ssh/${key}" >> ${hwd}/.bashrc


# Modify /etc/hosts on the server
sed "s/127.0/# 127.0/" < /etc/hosts > conf/nhosts
# for i in $(seq 1 $num_clusters)
# do
#     echo "${$(tail -$num_clusters conf/clusterIPs)[$((2*${i}-1))]} master${i}" >> nhosts
# done

lines=$(tail -$num_clusters conf/clusterIPs)
SAVEIFS=$IFS
IFS=$'\n'
lines=($lines)
IFS=$SAVEIFS

for (( i=0; i<${#lines[@]}; i++ ))
do
    line=(${lines[$i]})
    echo "${line[0]} master$((i+1))" >> conf/nhosts
done

cat conf/clusterIPs >> conf/nhosts
sudo cp conf/nhosts /etc/hosts


# Add clients
for i in $(seq 1 $num_clients)
do
    ssh-keyscan slave${i} >> ${hwd}/.ssh/known_hosts
done
for i in $(seq 1 $num_clusters)
do
    ssh-keyscan master${i} >> ${hwd}/.ssh/known_hosts
done

# Disable firewalls on clients
sudo ufw disable
sudo ufw status
for w in $(seq 1 $num_clients)
do
    ssh slave${w} 'sudo ufw disable; sudo ufw status'
done

# Modify /etc/hosts on the clients
for (( i=0; i<${#lines[@]}; i++ ))
do
    line=(${lines[$i]})
    echo "${line[0]} master" > conf/clusterIPs_$((i+1))
    start=$((2+${num_workers}*${i}))
    end=$((1+${num_workers}*((${i}+1))))
    worker_lines=$(sed -n "$start,$end p" conf/clusterIPs)
    SAVEIFS=$IFS
    IFS=$'\n'
    worker_lines=($worker_lines)
    IFS=$SAVEIFS
    for (( j=0; j<${#worker_lines[@]}; j++ ))
    do
        line=(${worker_lines[$j]})
        echo "${line[0]} slave$((j+1))" >> conf/clusterIPs_$((i+1))
    done
done

evalcmd='eval `ssh-agent -s`'
for i in $(seq 1 $num_clusters)
do
    start=$((1+${num_workers}*$((i-1))))
    end=$((${num_workers}*${i}))

    scp ${hwd}/.ssh/${key} cc@master${i}:${hwd}/.ssh
    scp conf/clusterIPs_${i} cc@master${i}:${hwd}/clusterIPs

    ssh cc@master${i} \
    "echo ${evalcmd} >> ${hwd}/.bashrc;
    echo 'ssh-add ${hwd}/.ssh/${key}' >> ${hwd}/.bashrc;
    sed \"s/127.0/# 127.0/\" < /etc/hosts > nhosts;
    cat clusterIPs >> nhosts;
    sudo cp nhosts /etc/hosts"

    for j in $(seq $start $end)
    do
        scp ${hwd}/.ssh/${key} cc@slave${j}:${hwd}/.ssh
        scp conf/clusterIPs_${i} cc@slave${j}:${hwd}/clusterIPs
        ssh cc@slave${j} \
        "echo ${evalcmd} >> ${hwd}/.bashrc;
        echo 'ssh-add ${hwd}/.ssh/${key}' >> ${hwd}/.bashrc;
        sed \"s/127.0/# 127.0/\" < /etc/hosts > nhosts;
        cat clusterIPs >> nhosts;
        sudo cp nhosts /etc/hosts"
    done
done

################################################################################
################################################################################



################################################################################
######################## Download and Install packages #########################

while test $# -gt 0
do
    case "$1" in
        java)
            echo "Install java"
            install_java
            ;;
        hadoop)
            echo "Install hadoop"
            install_hadoop
            ;;
        spark)
            echo "Install spark"
            install_spark
            ;;
        hibech)
            echo "Install hibench"
            install_hibench
            ;;
        npb)
            echo "Install npb"
            install_npb
            ;;
        *) echo "Bad argument $1"
            ;;
    esac
    shift
done



################################################################################
################################################################################



################################################################################
#################### Dispatch DPS and Change Configurations ####################


# Enable msr tools, Copy and compile RAPL, Set perf event configuration, Copy DPS
sudo modprobe msr
sudo sysctl -n kernel.perf_event_paranoid=-1
for w in $(seq 1 $num_clients);
do
    scp -r ${hwd}/DPS cc@slave${w}:${hwd}/
    ssh slave${w} "cp -r ${hwd}/DPS/RAPL ${hwd}/RAPL"
    ssh slave${w} \
    "sudo modprobe msr;
    sudo sysctl -n kernel.perf_event_paranoid=-1;
    cd RAPL; gcc RaplPowerMonitor_1s.c -o RaplPowerMonitor_1s -lm;"
done


# Build DPS
python3 -m pip install --upgrade pip build numpy
python3 -m pip install ${hwd}/DPS
for w in $(seq 1 $num_clients);
do
    scp -r ${hwd}/DPS cc@slave${w}:${hwd}/
    ssh slave${i} \
    "python3 -m pip install --upgrade pip build numpy;
    python3 -m pip install ${hwd}/DPS"
done

################################################################################
################################################################################



