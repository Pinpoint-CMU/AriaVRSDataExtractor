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
    os.makedirs(dir, exist_ok=True)

    with open(dir / "train.vvk", "w+") as outfile:
        outfile.writelines(train_data)

    with open(dir / "val.vvk", "w+") as outfile:
        outfile.writelines(val_data)

    with open(dir / "test.vvk", "w+") as outfile:
        outfile.writelines(test_data)
