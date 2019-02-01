#!/bin/sh

while true
do

 df -h |grep xvda > usage_output.txt
 python3 usage_detect_2.0.py
 sleep 7200

done
