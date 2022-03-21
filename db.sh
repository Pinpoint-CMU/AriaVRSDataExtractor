#!/bin/bash
for var in "$@"
do
  dir=$(dirname -- "$var")
  filename=$(basename -- "$var")
  sqlite3 -header -csv "$var" "SELECT \
    timestamp, \
    raw_acceleration_x as accX, \
    raw_acceleration_y as accY, \
    raw_acceleration_z as accZ, \
    raw_angular_x as gyroX, \
    raw_angular_y as gyroY, \
    raw_angular_z as gyroZ, \
    raw_magnetic_x as magX, \
    raw_magnetic_y as magY, \
    raw_magnetic_z as magZ \
    FROM imu;" > "$dir/$filename"_imu.csv
  sqlite3 -header -csv "$var" "SELECT \
    timestamp, \
    major, \
    minor, \
    rssi \
    FROM beacons \
    WHERE major = 65502 \
    AND rssi != 0 \
    ;" > "$dir/$filename"_ble.csv
done
