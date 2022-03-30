import csv
import sys
from pathlib import Path
from typing import Optional

import numpy as np

from bezier import get_bezier_cubic


def interpolate_gt(gt_data):
    gt_timestamps = np.array([float(row["#timestamp"]) for row in gt_data])
    gt_points_x = np.stack(
        [
            gt_timestamps,
            np.array([float(row["p_RS_R_x [m]"]) for row in gt_data]),
        ],
        axis=-1,
    )
    gt_points_y = np.stack(
        [
            gt_timestamps,
            np.array([float(row["p_RS_R_y [m]"]) for row in gt_data]),
        ],
        axis=-1,
    )
    gt_points_z = np.stack(
        [
            gt_timestamps,
            np.array([float(row["p_RS_R_z [m]"]) for row in gt_data]),
        ],
        axis=-1,
    )
    curves_x = get_bezier_cubic(gt_points_x)
    curves_y = get_bezier_cubic(gt_points_y)
    curves_z = get_bezier_cubic(gt_points_z)
    return curves_x, curves_y, curves_z, gt_timestamps


def process(alignment: Path):
    with open(alignment, "r") as alignment_file:
        alignment_reader = csv.DictReader(alignment_file, skipinitialspace=True)
        for truth_idx, match in enumerate(alignment_reader):
            db_file, aria_file, scale, offset, db_offset, aria_offset = (
                match[key]
                for key in [
                    "db_file",
                    "aria_file",
                    "scale",
                    "offset",
                    "db_offset",
                    "aria_offset",
                ]
            )
            scale, offset, db_offset, aria_offset = tuple(
                map(float, [scale, offset, db_offset, aria_offset])
            )
            db_to_aria_time = (
                lambda time: (time - offset + db_offset - aria_offset) / scale
            )
            ble_data_ungrouped, gt_data = [], []
            with open(alignment.parent / (db_file + "_ble.csv"), "r") as ble_csv, open(
                alignment.parent / (aria_file + ".euroc"), "r"
            ) as gt_csv:
                ble_reader = csv.DictReader(ble_csv, skipinitialspace=True)
                ble_data_ungrouped.extend([row for row in ble_reader])
                gt_reader = csv.DictReader(gt_csv, skipinitialspace=True)
                gt_data.extend([row for row in gt_reader])

            ble_data = []
            ble_t: Optional[str] = None
            cur_t_bles = []
            for data in ble_data_ungrouped:
                if ble_t != data["timestamp"]:
                    if ble_t is not None:
                        while float(data["timestamp"]) - float(ble_t) > 1.2:
                            print("No Beacons read for timestamp:", ble_t)
                            ble_data.append({"timestamp": ble_t, "ble": []})
                            ble_t = str(float(ble_t) + 1)
                        ble_data.append({"timestamp": ble_t, "ble": cur_t_bles})
                    ble_t = data["timestamp"]
                    cur_t_bles = []
                else:
                    cur_t_bles.append(
                        {
                            "major": int(data["major"]),
                            "minor": int(data["minor"]),
                            "rssi": int(data["rssi"]),
                        }
                    )

            curves_x, curves_y, curves_z, gt_timestamps = interpolate_gt(gt_data)
            output_data = []
            for data in ble_data:
                ble_timestamp = db_to_aria_time(float(data["timestamp"]))
                idx = np.searchsorted(gt_timestamps, ble_timestamp, side="right")
                if idx > 0 and idx < len(gt_timestamps):
                    t = (ble_timestamp - gt_timestamps[idx - 1]) / (
                        gt_timestamps[idx] - gt_timestamps[idx - 1]
                    )
                    assert t >= 0 and t <= 1
                    beacon_str = ";".join(
                        [f"{b['minor']},{b['rssi']}" for b in data["ble"]]
                    )
                    output_data.append(
                        f"{curves_x[idx - 1](t)[1]},{curves_y[idx - 1](t)[1]},{curves_z[idx - 1](t)[1]}:{beacon_str}"
                    )

            assert len(output_data) > 0
            outfilename = alignment.parent / f"traj_{truth_idx}.vvk"
            print("Writing", len(output_data), "rows to", outfilename)
            with open(alignment.parent / outfilename, "w+") as outfile:
                for row in output_data:
                    outfile.write(f"{row}\n")


if __name__ == "__main__":
    for alignment in sys.argv[1:]:
        process(Path(alignment).resolve())
