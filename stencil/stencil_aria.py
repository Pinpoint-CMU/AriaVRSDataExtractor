import csv
import json
import sys
from pathlib import Path


def write_files(filename: Path):
    time_filename = filename.parent / (str(filename.stem) + "_Time_1.csv")
    time_fields = ["timestamp", "realtime"]
    imu_filename = filename.parent / (str(filename.stem) + "_IMU_1.csv")
    imu_fields = ["timestamp", "accX", "accY", "accZ", "gyroX", "gyroY", "gyroZ"]
    euroc_filename = filename.parent / (str(filename.stem) + ".euroc")
    euroc_fields = [
        "#timestamp",
        "p_RS_R_x [m]",
        "p_RS_R_y [m]",
        "p_RS_R_z [m]",
        "q_RS_w []",
        "q_RS_x []",
        "q_RS_y []",
        "q_RS_z []",
        "v_RS_R_x [m s^-1]",
        "v_RS_R_y [m s^-1]",
        "v_RS_R_z [m s^-1]",
        "b_w_RS_S_x [rad s^-1]",
        "b_w_RS_S_y [rad s^-1]",
        "b_w_RS_S_z [rad s^-1]",
        "b_a_RS_S_x [m s^-2]",
        "b_a_RS_S_y [m s^-2]",
        "b_a_RS_S_z [m s^-2]",
    ]
    with open(time_filename, "w+") as time_csvfile, open(
        imu_filename, "w+"
    ) as imu_csvfile, open(euroc_filename, "w+") as euroc_file, open(
        filename, "r"
    ) as jsonfile:
        time_writer = csv.DictWriter(time_csvfile, time_fields)
        imu_writer = csv.DictWriter(imu_csvfile, imu_fields)
        time_writer.writeheader()
        imu_writer.writeheader()
        euroc_file.write(", ".join(euroc_fields) + "\n")

        for row in json.load(jsonfile):
            time_writer.writerow(
                {
                    "timestamp": row["timestamp"],
                    "realtime": row["timestamp"],
                }
            )
            imu_writer.writerow(
                {
                    "timestamp": row["timestamp"],
                    "accX": row["accX"],
                    "accY": row["accY"],
                    "accZ": row["accZ"],
                    "gyroX": row["ang_velX"],
                    "gyroY": row["ang_velY"],
                    "gyroZ": row["ang_velZ"],
                }
            )
            euroc_file.write(
                ", ".join(
                    [
                        str(row["timestamp"]),
                        str(row["posX"]),
                        str(row["posY"]),
                        str(row["posZ"]),
                        str(row["orientW"]),
                        str(row["orientX"]),
                        str(row["orientY"]),
                        str(row["orientZ"]),
                        "0.0",
                        "0.0",
                        "0.0",
                        "0.0",
                        "0.0",
                        "0.0",
                        "0.0",
                        "0.0",
                        "0.0",
                    ]
                )
                + "\n"
            )


def make_valid_json(filename: Path) -> Path:
    new_filename = filename.parent / (str(filename.stem) + "_valid.json")
    with open(filename, "r") as infile, open(new_filename, "w+") as outfile:
        outfile.write("[")
        for row in infile:
            if row == "}{\n":
                outfile.write("},{\n")
            else:
                outfile.write(row)
        outfile.write("]")
    return new_filename


def process(filename: Path):
    assert filename.suffix == ".json", filename
    valid_json = make_valid_json(filename)
    write_files(valid_json)


if __name__ == "__main__":
    for filename in sys.argv[1:]:
        process(Path(filename).resolve())
