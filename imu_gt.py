import csv
import json
import logging
import sys
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation, Slerp
from tqdm import tqdm

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


def to_aria_frame(orientations: Rotation, gt_orientations: Rotation, R_cam_rgb):
    R_local_cam = gt_orientations

    R_rgb_phone = (
        Rotation.from_euler("z", 90, degrees=True)
        * Rotation.from_euler("y", 180, degrees=True)
        * Rotation.from_euler("x", -45, degrees=True)
    )

    R_local_phone = R_local_cam * R_cam_rgb * R_rgb_phone
    R_ios_phone = orientations
    R_local_ios = R_local_phone * R_ios_phone.inv()
    R_avg = R_local_ios.as_matrix().mean(axis=0)
    U, _, V_t = np.linalg.svd(R_avg, full_matrices=True)
    D_ = np.diag([1, 1, np.linalg.det(U @ V_t)])
    R_avg = U @ D_ @ V_t
    R_avg = Rotation.from_matrix(R_avg)
    R_local_phone = R_avg * R_ios_phone

    return R_local_phone


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


def get_gt_imu(gt_imu_data):
    timestamps = np.array([float(row["timestamp"]) for row in gt_imu_data])
    imu = np.array(
        [
            [
                float(row["accX"]),
                float(row["accY"]),
                float(row["accZ"]),
                float(row["gyroX"]),
                float(row["gyroY"]),
                float(row["gyroZ"]),
            ]
            for row in gt_imu_data
        ]
    )
    return timestamps, imu


def interpolate_gt(
    timestamps, points, orientations: Rotation, gt_imu_timestamps, gt_imu
):
    curves_x = get_bezier_cubic(np.stack([timestamps, points[:, 0]], axis=-1))
    curves_y = get_bezier_cubic(np.stack([timestamps, points[:, 1]], axis=-1))
    curves_z = get_bezier_cubic(np.stack([timestamps, points[:, 2]], axis=-1))
    curves_orient = Slerp(timestamps, orientations)
    curves_imu = [
        get_bezier_cubic(np.stack([gt_imu_timestamps, gt_imu[:, i]], axis=-1))
        for i in range(gt_imu.shape[1])
    ]

    return curves_x, curves_y, curves_z, curves_orient, curves_imu


def process(alignment: Path, R: Rotation, T):
    with open(alignment, "r") as alignment_file:
        alignment_reader = csv.DictReader(
            alignment_file, skipinitialspace=True)
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
            logging.info(f"Processing {aria_file}->{db_file}")
            logging.info("Reading data files")
            scale, offset, db_offset, aria_offset = tuple(
                map(float, [scale, offset, db_offset, aria_offset])
            )
            db_to_aria_time = (
                lambda time: (time - offset + db_offset - aria_offset) / scale
            )
            imu_data, gt_data, gt_imu_data = [], [], []
            with open(alignment.parent / (db_file + "_imu.csv"), "r") as imu_csv, open(
                alignment.parent / (aria_file + ".euroc"), "r"
            ) as gt_csv, open(
                alignment.parent / (aria_file + "_IMU_1.csv"), "r"
            ) as gt_imu_csv:
                imu_reader = csv.DictReader(imu_csv, skipinitialspace=True)
                imu_data.extend([row for row in imu_reader])
                gt_reader = csv.DictReader(gt_csv, skipinitialspace=True)
                gt_data.extend([row for row in gt_reader])
                gt_imu_reader = csv.DictReader(
                    gt_imu_csv, skipinitialspace=True)
                gt_imu_data.extend([row for row in gt_imu_reader])

            logging.info("Interpolating data")
            gt_timestamps = get_timestamps(gt_data)
            gt_points = get_positions(gt_data)
            gt_orientations = get_orientations(gt_data)
            gt_imu_timestamps, gt_imu = get_gt_imu(gt_imu_data)
            gt_points, gt_orientations = to_rig(gt_points, gt_orientations)
            gt_points, gt_orientations = to_rgb(
                gt_points, gt_orientations, R, T)
            curves_x, curves_y, curves_z, curves_orient, curves_gt_imu = interpolate_gt(
                gt_timestamps, gt_points, gt_orientations, gt_imu_timestamps, gt_imu
            )
            output_data = []
            output_gt_orient = []
            output_phone_gyro_orient = []
            output_phone_mag_orient = []
            for data in tqdm(imu_data):
                imu_timestamp = db_to_aria_time(float(data["timestamp"]))
                idx = np.searchsorted(
                    gt_timestamps, imu_timestamp, side="right")
                idx_gt_imu = np.searchsorted(
                    gt_imu_timestamps, imu_timestamp, side="right"
                )
                if idx > 0 and idx < len(gt_timestamps):
                    t = (imu_timestamp - gt_timestamps[idx - 1]) / (
                        gt_timestamps[idx] - gt_timestamps[idx - 1]
                    )
                    t_gt_imu = (imu_timestamp - gt_imu_timestamps[idx_gt_imu - 1]) / (
                        gt_imu_timestamps[idx_gt_imu]
                        - gt_imu_timestamps[idx_gt_imu - 1]
                    )
                    assert t >= 0 and t <= 1
                    orientation = curves_orient(imu_timestamp).as_quat()
                    stencilAccX = curves_gt_imu[0][idx_gt_imu - 1](t_gt_imu)[1]
                    stencilAccY = curves_gt_imu[1][idx_gt_imu - 1](t_gt_imu)[1]
                    stencilAccZ = curves_gt_imu[2][idx_gt_imu - 1](t_gt_imu)[1]
                    stencilGyroX = curves_gt_imu[3][idx_gt_imu - 1](t_gt_imu)[
                        1]
                    stencilGyroY = curves_gt_imu[4][idx_gt_imu - 1](t_gt_imu)[
                        1]
                    stencilGyroZ = curves_gt_imu[5][idx_gt_imu - 1](t_gt_imu)[
                        1]

                    output_gt_orient.append(Rotation.from_quat(orientation))
                    output_phone_gyro_orient.append(
                        Rotation.from_quat(
                            [
                                float(data["orientX"]),
                                float(data["orientY"]),
                                float(data["orientZ"]),
                                float(data["orientW"]),
                            ]
                        )
                    )
                    output_phone_mag_orient.append(
                        Rotation.from_quat(
                            [
                                float(data["magOrientX"]),
                                float(data["magOrientY"]),
                                float(data["magOrientZ"]),
                                float(data["magOrientW"]),
                            ]
                        )
                    )
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
                            "stencilAccX": stencilAccX,
                            "stencilAccY": stencilAccY,
                            "stencilAccZ": stencilAccZ,
                            "stencilGyroX": stencilGyroX,
                            "stencilGyroY": stencilGyroY,
                            "stencilGyroZ": stencilGyroZ,
                            "orientW": orientation[3],
                            "orientX": orientation[0],
                            "orientY": orientation[1],
                            "orientZ": orientation[2],
                            "processedPosX": curves_x[idx - 1](t)[1],
                            "processedPosY": curves_y[idx - 1](t)[1],
                            "processedPosZ": curves_z[idx - 1](t)[1],
                        }
                    )

            assert len(output_data) > 0

            logging.info("Rotating phone orientations to aria frame")
            output_gt_orient = Rotation.concatenate(output_gt_orient)
            output_phone_gyro_orient = Rotation.concatenate(
                output_phone_gyro_orient)
            output_phone_mag_orient = Rotation.concatenate(
                output_phone_mag_orient)
            output_phone_gyro_orient = to_aria_frame(
                output_phone_gyro_orient, output_gt_orient, R
            ).as_quat()
            output_phone_mag_orient = to_aria_frame(
                output_phone_mag_orient, output_gt_orient, R
            ).as_quat()

            for idx, (d, gyro_orient, mag_orient) in enumerate(
                zip(output_data, output_phone_gyro_orient, output_phone_mag_orient)
            ):
                output_data[idx] = {
                    **d,
                    "phoneGyroOrientW": gyro_orient[3],
                    "phoneGyroOrientX": gyro_orient[0],
                    "phoneGyroOrientY": gyro_orient[1],
                    "phoneGyroOrientZ": gyro_orient[2],
                    "phoneMagOrientW": mag_orient[3],
                    "phoneMagOrientX": mag_orient[0],
                    "phoneMagOrientY": mag_orient[1],
                    "phoneMagOrientZ": mag_orient[2],
                }

            outfilename = alignment.parent / f"traj_{truth_idx}.csv"
            logging.info(f"Writing {len(output_data)} rows to {outfilename}")
            with open(alignment.parent / outfilename, "w+") as outfile:
                writer = csv.DictWriter(
                    outfile, fieldnames=list(output_data[0].keys()))
                writer.writeheader()
                for row in tqdm(output_data):
                    writer.writerow(row)


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s",
        level=logging.INFO,
        datefmt="%H:%M:%S",
    )
    R, T = load_calib()
    for alignment in sys.argv[1:]:
        process(Path(alignment).resolve(), R, T)
