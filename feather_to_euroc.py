import sys
from pathlib import Path

import pandas as pd

if __name__ == "__main__":
    for file in [Path(f).resolve() for f in sys.argv[1:]]:
        assert file.suffix == ".feather"
        reader = pd.read_feather(file)
        with open(
            file.parent / (file.name.removesuffix(".feather") + ".euroc"), "w+"
        ) as outfile:
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
            for idx, row in reader.iterrows():
                outfile.write(
                    ", ".join(
                        [
                            str(idx),
                            str(row["processedPosX"]),
                            str(row["processedPosY"]),
                            str(row["processedPosZ"]),
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
                if idx > 8000:
                    break
