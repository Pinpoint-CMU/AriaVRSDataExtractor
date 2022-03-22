#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  VRS_EXEC="$SCRIPT_DIR/vivek_vrs"
elif [[ "$OSTYPE" == "darwin"* ]]; then
  VRS_EXEC="$SCRIPT_DIR/vivek_vrs_mac"
else
  echo "Unsupported OS"
  exit 1
fi

for val in "$@"
do
  dir=$(cd -- "$SCRIPT_DIR/$val" && pwd)
  echo "Running on $dir"
  find "$dir" -type f -name "*.vrs" | xargs -I {} "$VRS_EXEC" "{}"
  find "$dir" -type f -name "*.db" | xargs -I {} "$SCRIPT_DIR/db.sh" "{}"
  python3 "$SCRIPT_DIR/imu_alignment.py" "$dir" > "$dir/alignment.csv"
done
