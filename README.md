# AriaVRSDataExtractor

Tool to extract IMU data from Aria VRS files and time-sync with IMU data from recorded phone db files.
Also reads GT poses from Aria .euroc file and transforms them to a fixed world frame, with up-sampling to IMU data rate.

Tested on Mac OS.
```bash
brew install boost cppformat xxhash lz4 zstd
bash run.sh <path-to-vrs-and-phone-db-and-euroc-dir>
```
