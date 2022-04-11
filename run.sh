#!/bin/bash

# Sort by timestamps and remove the first 8 values
# ls *.euroc | xargs -I {} -- sh -c 'printf "{}, "; sed -n "2 p" {}' | awk -F ", " '{print $1, $2}' | sort -k2 -n | head -n 8 | cut -d ' ' -f 1 | xargs rm

SPLIT_GEN_FILES=true
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
  # find "$dir" -type f -name "*.vrs" | xargs -I {} "$VRS_EXEC" "{}"
  # find "$dir" -type f -name "*.db" | xargs -I {} "$SCRIPT_DIR/db.sh" "{}"
  # python3 "$SCRIPT_DIR/imu_alignment.py" "$dir" > "$dir/alignment.csv"
  # python3 "$SCRIPT_DIR/imu_gt.py" "$dir/alignment.csv"
  # python3 "$SCRIPT_DIR/ble_gt.py" "$dir/alignment.csv"
  if [ "$SPLIT_GEN_FILES" = true ]; then
    find "$dir" -type f -name "traj*.csv" | xargs python3 "$SCRIPT_DIR/split_imu.py"
    find "$dir" -type f -name "traj*.vvk" | xargs python3 "$SCRIPT_DIR/split_ble.py"
  fi
done
