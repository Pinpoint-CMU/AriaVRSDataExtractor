import os
import sys
from pathlib import Path

if __name__ == "__main__":
    files = [Path(f).resolve() for f in sys.argv[1:]]
    assert len(files) > 0
    data = []
    for file in files:
        with open(file, "r") as f:
            for row in f:
                data.append(row)
    train_split = int(0.7 * len(data))
    val_split = int(0.1 * len(data))

    train_data = data[:train_split]
    val_data = data[train_split : train_split + val_split]
    test_data = data[train_split + val_split :]

    dir = files[0].parent / (str(files[0].parent.name) + "_vvk")
    train_dir = dir / "train"
    val_dir = dir / "val"
    test_dir = dir / "test"
    os.makedirs(dir, exist_ok=True)
    os.makedirs(train_dir, exist_ok=True)
    os.makedirs(val_dir, exist_ok=True)
    os.makedirs(test_dir, exist_ok=True)

    with open(train_dir / "traj_0.vvk", "w+") as outfile:
        outfile.writelines(train_data)

    with open(val_dir / "traj_0.vvk", "w+") as outfile:
        outfile.writelines(val_data)

    with open(test_dir / "traj_0.vvk", "w+") as outfile:
        outfile.writelines(test_data)
