import csv
import sys
from pathlib import Path

from rosbags.rosbag1 import Writer
from rosbags.serde import cdr_to_ros1, serialize_cdr
from rosbags.typesys.types import geometry_msgs__msg__Point as Point


def process(input: Path, output: Path):
    assert input.suffix == ".csv"
    with Writer(output) as writer:
        topic = "/position"
        msgtype = Point.__msgtype__
        connection = writer.add_connection(topic, msgtype)

        for i in range(1000):
            message = Point(x=1 + i, y=2 + i, z=3)
            writer.write(
                connection, i + 1, cdr_to_ros1(serialize_cdr(message, msgtype), msgtype)
            )


if __name__ == "__main__":
    for file in sys.argv[1:]:
        infile = Path(file).resolve()
        outfile = infile.parent / (infile.stem + ".bag")
        process(infile, outfile)
