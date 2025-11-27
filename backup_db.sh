#!/bin/bash
# Script to backup database for Gas Gauge

set -o xtrace

docker container stop gas-gauge
sleep 5
rm -vf /home/pi/backup/gas_gauge.db
cp /home/pi/code/container_data/gas_gauge.db /home/pi/backup/gas_gauge.db
docker container start gas-gauge

