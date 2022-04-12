import csv
import sys
from pathlib import Path

if __name__ == "__main__":
    for file in [Path(f).resolve() for f in sys.argv[1:]]:
        assert file.suffix == ".csv"
        with open(file, "r") as csvfile, open(
            file.parent / (file.name.removesuffix(".csv") + ".euroc"), "w+"
        ) as outfile:
            reader = csv.DictReader(csvfile)
            outfile.write(
                ", ".join(
                    [
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
                )
                + "\n"
            )
            for idx, row in enumerate(reader):
                outfile.write(
                    ", ".join(
                        [
                            str(idx),
                            row["processedPosX"],
                            row["processedPosY"],
                            row["processedPosZ"],
                            row["orientW"],
                            row["orientX"],
                            row["orientY"],
                            row["orientZ"],
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
                if idx > 8000:
                    break
