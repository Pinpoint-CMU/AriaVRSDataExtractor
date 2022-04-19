import csv
import math
import sys
import time
from pathlib import Path

import numpy as np
from rosbags.rosbag1 import Writer
from rosbags.serde import cdr_to_ros1, serialize_cdr
from rosbags.typesys.types import builtin_interfaces__msg__Time as Time
from rosbags.typesys.types import geometry_msgs__msg__Point as Point
from rosbags.typesys.types import geometry_msgs__msg__Pose as Pose
from rosbags.typesys.types import \
    geometry_msgs__msg__PoseStamped as PoseStamped
from rosbags.typesys.types import \
    geometry_msgs__msg__PoseWithCovariance as PoseWithCovariance
from rosbags.typesys.types import geometry_msgs__msg__Quaternion as Quaternion
from rosbags.typesys.types import geometry_msgs__msg__Transform as Transform
from rosbags.typesys.types import \
    geometry_msgs__msg__TransformStamped as TransformStamped
from rosbags.typesys.types import geometry_msgs__msg__Twist as Twist
from rosbags.typesys.types import \
    geometry_msgs__msg__TwistWithCovariance as TwistWithCovariance
from rosbags.typesys.types import geometry_msgs__msg__Vector3 as Vector3
from rosbags.typesys.types import nav_msgs__msg__Odometry as Odometry
from rosbags.typesys.types import nav_msgs__msg__Path as RosPath
from rosbags.typesys.types import sensor_msgs__msg__Imu as Imu
from rosbags.typesys.types import sensor_msgs__msg__MagneticField as Mag
from rosbags.typesys.types import std_msgs__msg__Header as Header
from rosbags.typesys.types import tf2_msgs__msg__TFMessage as TFMessage
from tqdm import tqdm


def process(input: Path, output: Path):
    assert input.suffix == ".csv"
    with Writer(output) as writer:
        traj_topic = "/traj"
        traj_msgtype = Odometry.__msgtype__
        traj_connection = writer.add_connection(traj_topic, traj_msgtype)
        imu_topic = "/imu"
        imu_msgtype = Imu.__msgtype__
        imu_connection = writer.add_connection(imu_topic, imu_msgtype)
        path_topic = "/path"
        path_msgtype = RosPath.__msgtype__
        path_connection = writer.add_connection(path_topic, path_msgtype)
        mag_topic = "/mag"
        mag_msgtype = Mag.__msgtype__
        mag_connection = writer.add_connection(mag_topic, mag_msgtype)
        start_time = time.time_ns()
        start_time_s = int(start_time / 1e9)
        start_time_ns = int(start_time % int(1e9))
        csv_start_time = None

        writer.write(
            writer.add_connection("/tf", TFMessage.__msgtype__),
            start_time,
            cdr_to_ros1(
                serialize_cdr(
                    TFMessage(
                        transforms=[
                            TransformStamped(
                                header=Header(
                                    frame_id="map",
                                    stamp=Time(sec=start_time_s, nanosec=start_time_ns),
                                ),
                                child_frame_id="traj",
                                transform=Transform(
                                    translation=Vector3(x=0, y=0, z=0),
                                    rotation=Quaternion(x=0, y=0, z=0, w=1),
                                ),
                            )
                        ]
                    ),
                    TFMessage.__msgtype__,
                ),
                TFMessage.__msgtype__,
            ),
        )

        poses = []
        timestamps = []
        times = []

        with open(input, "r") as csvfile:
            lines = sum(1 for line in csvfile)
            csvfile.seek(0)
            csv_reader = csv.DictReader(csvfile)
            for row in tqdm(csv_reader, total=lines):
                # timestamp,iphoneAccX,iphoneAccY,iphoneAccZ,iphoneGyroX,iphoneGyroY,iphoneGyroZ,iphoneMagX,iphoneMagY,iphoneMagZ,
                # orientW,orientX,orientY,orientZ,
                # processedPosX,processedPosY,processedPosZ
                if csv_start_time is None:
                    csv_start_time = float(row["timestamp"])
                dt = float(row["timestamp"]) - csv_start_time

                times.append(
                    Time(
                        sec=start_time_s + int(math.floor(dt / 1e9)),
                        nanosec=int(math.ceil(dt % 1e9)),
                    )
                )
                timestamps.append(start_time + int(math.floor(dt)))

                odometry = Odometry(
                    header=Header(
                        frame_id="traj",
                        stamp=Time(
                            sec=start_time_s + int(math.floor(dt / 1e9)),
                            nanosec=int(math.ceil(dt % 1e9)),
                        ),
                    ),
                    child_frame_id="traj",
                    pose=PoseWithCovariance(
                        pose=Pose(
                            position=Point(
                                x=float(row["processedPosX"]),
                                y=float(row["processedPosY"]),
                                z=float(row["processedPosZ"]),
                            ),
                            orientation=Quaternion(
                                x=float(row["orientX"]),
                                y=float(row["orientY"]),
                                z=float(row["orientZ"]),
                                w=float(row["orientW"]),
                            ),
                        ),
                        covariance=np.zeros((36,), dtype=np.float64),
                    ),
                    twist=TwistWithCovariance(
                        twist=Twist(linear=Vector3(0, 0, 0), angular=Vector3(0, 0, 0)),
                        covariance=np.zeros((36,), dtype=np.float64),
                    ),
                )
                writer.write(
                    traj_connection,
                    start_time + int(math.floor(dt)),
                    cdr_to_ros1(serialize_cdr(odometry, traj_msgtype), traj_msgtype),
                )

                poses.append(
                    PoseStamped(
                        header=Header(
                            frame_id="path",
                            stamp=Time(
                                sec=start_time_s + int(math.floor(dt / 1e9)),
                                nanosec=int(math.ceil(dt % 1e9)),
                            ),
                        ),
                        pose=Pose(
                            position=Point(
                                x=float(row["processedPosX"]),
                                y=float(row["processedPosY"]),
                                z=float(row["processedPosZ"]),
                            ),
                            orientation=Quaternion(
                                x=float(row["orientX"]),
                                y=float(row["orientY"]),
                                z=float(row["orientZ"]),
                                w=float(row["orientW"]),
                            ),
                        ),
                    )
                )

                # timestamp,iphoneAccX,iphoneAccY,iphoneAccZ,iphoneGyroX,iphoneGyroY,iphoneGyroZ,iphoneMagX,iphoneMagY,iphoneMagZ,
                imu = Imu(
                    header=Header(
                        frame_id="imu",
                        stamp=Time(
                            sec=start_time_s + int(math.floor(dt / 1e9)),
                            nanosec=int(math.ceil(dt % 1e9)),
                        ),
                    ),
                    orientation=Quaternion(
                        x=float(row["orientX"]),
                        y=float(row["orientY"]),
                        z=float(row["orientZ"]),
                        w=float(row["orientW"]),
                    ),
                    orientation_covariance=np.zeros((9,), dtype=np.float64),
                    angular_velocity=Vector3(
                        x=float(row["iphoneGyroX"]),
                        y=float(row["iphoneGyroY"]),
                        z=float(row["iphoneGyroZ"]),
                    ),
                    angular_velocity_covariance=np.zeros((9,), dtype=np.float64),
                    linear_acceleration=Vector3(
                        x=float(row["iphoneAccX"]),
                        y=float(row["iphoneAccY"]),
                        z=float(row["iphoneAccZ"]),
                    ),
                    linear_acceleration_covariance=np.zeros((9,), dtype=np.float64),
                )
                writer.write(
                    imu_connection,
                    start_time + int(math.floor(dt)),
                    cdr_to_ros1(serialize_cdr(imu, imu_msgtype), imu_msgtype),
                )
                mag = Mag(
                    header=Header(
                        frame_id="mag",
                        stamp=Time(
                            sec=start_time_s + int(math.floor(dt / 1e9)),
                            nanosec=int(math.ceil(dt % 1e9)),
                        ),
                    ),
                    magnetic_field=Vector3(
                        x=float(row["iphoneMagX"]),
                        y=float(row["iphoneMagY"]),
                        z=float(row["iphoneMagZ"]),
                    ),
                    magnetic_field_covariance=np.zeros((9,), dtype=np.float64),
                )
                writer.write(
                    mag_connection,
                    start_time + int(math.floor(dt)),
                    cdr_to_ros1(serialize_cdr(mag, mag_msgtype), mag_msgtype),
                )

        for t, stamp in tqdm(
            zip(times[::10], timestamps[::10]), total=len(times[::10])
        ):
            writer.write(
                path_connection,
                stamp,
                cdr_to_ros1(
                    serialize_cdr(
                        RosPath(
                            header=Header(
                                frame_id="traj",
                                stamp=t,
                            ),
                            poses=poses,
                        ),
                        path_msgtype,
                    ),
                    path_msgtype,
                ),
            )


if __name__ == "__main__":
    for file in sys.argv[1:]:
        infile = Path(file).resolve()
        outfile = infile.parent / (infile.stem + ".bag")
        process(infile, outfile)
