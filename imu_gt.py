import csv
import sys
from pathlib import Path

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
            imu_data, gt_data = [], []
            with open(alignment.parent / (db_file + "_imu.csv"), "r") as imu_csv, open(
                alignment.parent / (aria_file + ".euroc"), "r"
            ) as gt_csv:
                imu_reader = csv.DictReader(imu_csv, skipinitialspace=True)
                imu_data.extend([row for row in imu_reader])
                gt_reader = csv.DictReader(gt_csv, skipinitialspace=True)
                gt_data.extend([row for row in gt_reader])

            curves_x, curves_y, curves_z, gt_timestamps = interpolate_gt(gt_data)
            output_data = []
            for data in imu_data:
                imu_timestamp = db_to_aria_time(float(data["timestamp"]))
                idx = np.searchsorted(gt_timestamps, imu_timestamp, side="right")
                if idx > 0 and idx < len(gt_timestamps):
                    t = (imu_timestamp - gt_timestamps[idx - 1]) / (
                        gt_timestamps[idx] - gt_timestamps[idx - 1]
                    )
                    assert t >= 0 and t <= 1
                    output_data.append(
                        {
                            "timestamp": float(imu_timestamp),
                            "iphoneAccX": float(data["accX"]),
                            "iphoneAccY": float(data["accY"]),
                            "iphoneAccZ": float(data["accZ"]),
                            "iphoneGyroX": float(data["gyroX"]),
                            "iphoneGyroY": float(data["gyroY"]),
                            "iphoneGyroZ": float(data["gyroZ"]),
                            "iphoneMagX": float(data["magX"]),
                            "iphoneMagY": float(data["magY"]),
                            "iphoneMagZ": float(data["magZ"]),
                            "orientW": float(data["orientW"]),
                            "orientX": float(data["orientX"]),
                            "orientY": float(data["orientY"]),
                            "orientZ": float(data["orientZ"]),
                            "processedPosX": curves_x[idx - 1](t),
                            "processedPosY": curves_y[idx - 1](t),
                            "processedPosZ": curves_z[idx - 1](t),
                        }
                    )

            assert len(output_data) > 0
            outfilename = alignment.parent / f"traj_{truth_idx}.csv"
            print("Writing", len(output_data), "rows to", outfilename)
            with open(alignment.parent / outfilename, "w+") as outfile:
                writer = csv.DictWriter(outfile, fieldnames=list(output_data[0].keys()))
                writer.writeheader()
                for row in output_data:
                    writer.writerow(row)


if __name__ == "__main__":
    for alignment in sys.argv[1:]:
        process(Path(alignment).resolve())
