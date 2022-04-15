import sys

from rosbags.rosbag1 import Reader
from rosbags.serde import deserialize_cdr, ros1_to_cdr

# create reader instance
with Reader(sys.argv[1]) as reader:
    # topic and msgtype information is available on .connections dictionary
    for connection in reader.connections.values():
        print(connection.topic, connection.msgtype)

    # iterate over messages
    if len(sys.argv) > 2:
        for connection, timestamp, rawdata in reader.messages():
            if connection.topic == sys.argv[2]:
                msg = deserialize_cdr(
                    ros1_to_cdr(rawdata, connection.msgtype), connection.msgtype
                )
                print(msg)
