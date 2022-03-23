import csv
import sys
from pathlib import Path

import numpy as np


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

            imu_timestamps = np.array(
                [db_to_aria_time(float(row["timestamp"])) for row in imu_data]
            )
            output_data = []
            for data in gt_data:
                gt_timestamp = float(data["#timestamp"])
                idx = np.searchsorted(imu_timestamps, gt_timestamp)
                if idx < len(output_data) - 1:
                    idx = (
                        idx + 1
                        if (gt_timestamp - imu_timestamps[idx]) ** 2
                        > (gt_timestamp - imu_timestamps[idx + 1]) ** 2
                        else idx
                    )
                if idx >= len(imu_timestamps):
                    break
                if idx > 0:
                    output_data.append(
                        {
                            "timestamp": float(gt_timestamp),
                            "iphoneAccX": float(imu_data[idx]["accX"]),
                            "iphoneAccY": float(imu_data[idx]["accY"]),
                            "iphoneAccZ": float(imu_data[idx]["accZ"]),
                            "iphoneGyroX": float(imu_data[idx]["gyroX"]),
                            "iphoneGyroY": float(imu_data[idx]["gyroY"]),
                            "iphoneGyroZ": float(imu_data[idx]["gyroZ"]),
                            "iphoneMagX": float(imu_data[idx]["magX"]),
                            "iphoneMagY": float(imu_data[idx]["magY"]),
                            "iphoneMagZ": float(imu_data[idx]["magZ"]),
                            "orientW": float(imu_data[idx]["orientW"]),
                            "orientX": float(imu_data[idx]["orientX"]),
                            "orientY": float(imu_data[idx]["orientY"]),
                            "orientZ": float(imu_data[idx]["orientZ"]),
                            "processedPosX": float(data["p_RS_R_x [m]"]),
                            "processedPosY": float(data["p_RS_R_y [m]"]),
                            "processedPosZ": float(data["p_RS_R_z [m]"]),
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
