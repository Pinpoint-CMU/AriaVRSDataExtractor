import csv
import sys
from pathlib import Path

import numpy as np
from matplotlib import pyplot as plt


def plot(file: Path):
    with open(file, "r") as f:
        reader = csv.DictReader(f)
        positionsX, positionsY, magX, magY, magZ = [], [], [], [], []
        for row in reader:
            positionsX.append(float(row["processedPosX"]))
            positionsY.append(float(row["processedPosY"]))
            magX.append(float(row["iphoneMagX"]))
            magY.append(float(row["iphoneMagY"]))
            magZ.append(float(row["iphoneMagZ"]))

        positionsX, positionsY, magX, magY, magZ = (
            np.array(positionsX),
            np.array(positionsY),
            np.array(magX),
            np.array(magY),
            np.array(magZ),
        )

        mag_xy_norm = np.sqrt(magX ** 2 + magY ** 2)
        magX /= mag_xy_norm
        magY /= mag_xy_norm
        magZ -= magZ.min()
        magZ /= magZ.max()

        _, ax = plt.subplots(figsize=(12, 16))
        ax.quiver(
            positionsX[::50],
            positionsY[::50],
            magX[::50],
            magY[::50],
            magZ[::50],
            scale=40,
        )
        plt.show()


if __name__ == "__main__":
    for file in sys.argv[1:]:
        plot(Path(file).resolve())
