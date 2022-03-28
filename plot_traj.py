import csv
import sys
from pathlib import Path

import numpy as np
from matplotlib import pyplot as plt


def plot_traj(filename: Path):
    reader = csv.DictReader(open(filename, "r"))
    txyz = np.array(
        [
            [
                float(row["timestamp"]),
                float(row["processedPosX"]),
                float(row["processedPosY"]),
                float(row["processedPosZ"]),
            ]
            for row in reader
        ]
    )
    _, axes = plt.subplots(2, 1)
    axes[0].plot(txyz[:, 1], txyz[:, 2])
    axes[1].plot(txyz[:, 1], txyz[:, 3])
    plt.show()


if __name__ == "__main__":
    for traj in sys.argv[1:]:
        plot_traj(Path(traj).resolve())
