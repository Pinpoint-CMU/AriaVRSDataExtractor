#!/bin/bash

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  VRS_EXEC="./vivek_vrs"
elif [[ "$OSTYPE" == "darwin"* ]]; then
  VRS_EXEC="./vivek_vrs_mac"
else
  echo "Unsupported OS"
  exit 1
fi

for var in "$@"
do
  dir=$(dirname -- "$var")
  ls "$dir/*.vrs" | xargs -I {} "$VRS_EXEC" "{}"
  ls "$dir/*.db" | xargs -I {} "./db.sh" "{}"
  python3 "./imu_alignment.py" "$dir" > "$dir/alignment.csv"
done
