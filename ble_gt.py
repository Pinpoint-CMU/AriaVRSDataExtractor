import csv
import json
import sys
from pathlib import Path
from typing import Optional

import numpy as np
from scipy.spatial.transform import Rotation

from bezier import get_bezier_cubic

aria_calib_file = Path("./1WM093700U1171_473758244165429.json").resolve()


def load_calib(calib_file=aria_calib_file):
    calibration_info = json.load(open(calib_file, "r"))
    assert (
        calibration_info["OriginSpecification"]["ChildLabel"] == "camera-slam-left"
    ), calibration_info["OriginSpecification"]["ChildLabel"]
    rgb = calibration_info["CameraCalibrations"][
        [
            i
            for i, _ in enumerate(calibration_info["CameraCalibrations"])
            if _["Label"] == "camera-rgb"
        ][0]
    ]
    assert rgb["Calibrated"] == True, rgb
    trans = rgb["T_Device_Camera"]["Translation"]
    rot = rgb["T_Device_Camera"]["UnitQuaternion"]
    rot = Rotation.from_quat([*rot[1], rot[0]])
    return rot, np.array(trans)


def to_rig(positions, orientations: Rotation):
    init_orient = orientations[0]
    init_trans = positions[0]
    positions -= init_trans
    positions = init_orient.apply(positions, inverse=True)
    orientations = init_orient.inv() * orientations
    return positions, orientations


def to_rgb(positions, orientations: Rotation, R: Rotation, T):
    positions -= T
    positions = R.apply(positions, inverse=True)
    orientations = R.inv() * orientations
    R_ref_rgb = Rotation.from_euler("y", 90, degrees=True)
    positions = R_ref_rgb.apply(positions)
    orientations = R_ref_rgb * orientations
    return positions, orientations


def get_timestamps(gt_data):
    return np.array([float(row["#timestamp"]) for row in gt_data])


def get_positions(gt_data):
    return np.array(
        [
            [
                float(row["p_RS_R_x [m]"]),
                float(row["p_RS_R_y [m]"]),
                float(row["p_RS_R_z [m]"]),
            ]
            for row in gt_data
        ]
    )


def get_orientations(gt_data):
    return Rotation.from_quat(
        np.array(
            [
                [
                    float(row["q_RS_x []"]),
                    float(row["q_RS_y []"]),
                    float(row["q_RS_z []"]),
                    float(row["q_RS_w []"]),
                ]
                for row in gt_data
            ]
        )
    )


def interpolate_gt(timestamps, points):
    curves_x = get_bezier_cubic(np.stack([timestamps, points[:, 0]], axis=-1))
    curves_y = get_bezier_cubic(np.stack([timestamps, points[:, 1]], axis=-1))
    curves_z = get_bezier_cubic(np.stack([timestamps, points[:, 2]], axis=-1))
    return curves_x, curves_y, curves_z


def process(alignment: Path, R: Rotation, T):
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

            gt_timestamps = get_timestamps(gt_data)
            gt_points = get_positions(gt_data)
            gt_orientations = get_orientations(gt_data)
            gt_points, gt_orientations = to_rig(gt_points, gt_orientations)
            gt_points, gt_orientations = to_rgb(gt_points, gt_orientations, R, T)
            curves_x, curves_y, curves_z = interpolate_gt(gt_timestamps, gt_points)
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
                        f"{ble_timestamp}:{curves_x[idx - 1](t)[1]},{curves_y[idx - 1](t)[1]},{curves_z[idx - 1](t)[1]}:{beacon_str}"
                    )

            assert len(output_data) > 0
            outfilename = alignment.parent / f"traj_{truth_idx}.vvk"
            print("Writing", len(output_data), "rows to", outfilename)
            with open(alignment.parent / outfilename, "w+") as outfile:
                for row in output_data:
                    outfile.write(f"{row}\n")


if __name__ == "__main__":
    R, T = load_calib()
    for alignment in sys.argv[1:]:
        process(Path(alignment).resolve(), R, T)
