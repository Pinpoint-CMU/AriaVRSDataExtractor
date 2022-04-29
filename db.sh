#!/bin/bash
for var in "$@"
do
  dir=$(dirname -- "$var")
  filename=$(basename -- "$var")
  sqlite3 -header -csv "$var" "SELECT \
    timestamp, \
    rotation_w as orientW, \
    rotation_x as orientX, \
    rotation_y as orientY, \
    rotation_z as orientZ, \
    geomag_rotation_w as magOrientW, \
    geomag_rotation_x as magOrientX, \
    geomag_rotation_y as magOrientY, \
    geomag_rotation_z as magOrientZ, \
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
  sqlite3 "$var" ".tables beac%" | xargs -I {} \
  sqlite3 -header -csv "$var" "SELECT \
    timestamp, \
    major, \
    minor, \
    rssi \
    FROM {} \
    WHERE major = 10004 \
    AND rssi != 0 \
    ;" > "$dir/$filename"_ble.csv
done
