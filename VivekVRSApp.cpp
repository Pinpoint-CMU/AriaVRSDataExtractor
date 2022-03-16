#include <fmt/core.h>
#include <fmt/format.h>
#include <vrs/RecordFileReader.h>
#include <iostream>

using namespace std;
using namespace vrs;

void readIMU(RecordFileReader& reader) {
  const StreamId id1 = reader.getStreamForType(RecordableTypeId::SlamImuData, 0);
  if (!id1.isValid()) {
    fmt::print(stderr, "Could not read IMU index 0");
  }
  const StreamId id2 = reader.getStreamForType(RecordableTypeId::SlamImuData, 1);
  if (!id2.isValid()) {
    fmt::print(stderr, "Could not read IMU index 1");
  }
}

void readVRSFile(string filePath) {
  RecordFileReader reader;
  if (reader.openFile(filePath) == 0) {
    readIMU(reader);
    reader.readAllRecords();
    reader.closeFile();
  } else {
    fmt::print(stderr, "Failed to open VRS file: {}\n", filePath);
  }
}

int main(int argc, char* argv[]) {
  if (argc < 2) {
    fmt::print(stderr, "USAGE: {} VRS_FILE...\n", argv[0]);
    return 1;
  }
  for (int i = 1; i < argc; ++i)
    readVRSFile(argv[1]);
  return 0;
}
