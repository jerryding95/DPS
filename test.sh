#!/bin/bash
while test $# -gt 0
do
    case "$1" in
        java)
            echo "Install java"
            # install_java
            ;;
        hadoop)
            echo "Install hadoop"
            # install_hadoop
            ;;
        spark)
            echo "Install spark"
            # install_spark
            ;;
        hibech)
            echo "Install hibench"
            # install_hibench
            ;;
        npb)
            echo "Install npb"
            # install_npb
            ;;
        *) echo "Bad argument $1"
            ;;
    esac
    shift
done