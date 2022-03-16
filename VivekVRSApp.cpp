#include <fmt/core.h>
#include <fmt/format.h>
#include <iostream>
#include <memory>

#include <vrs/RecordFileReader.h>
#include <vrs/RecordFormatStreamPlayer.h>
#include <vrs/oss/aria/BarometerMetadata.h>
#include <vrs/oss/aria/BluetoothBeaconMetadata.h>
#include <vrs/oss/aria/MotionSensorMetadata.h>
#include <vrs/oss/aria/WifiBeaconMetadata.h>

using namespace std;
using namespace vrs;

void printDataLayout(const CurrentRecord& r, DataLayout& datalayout) {
  fmt::print(
      "{:.3f} {} record, {} [{}]\n",
      r.timestamp,
      toString(r.recordType),
      r.streamId.getName(),
      r.streamId.getNumericName());
  datalayout.printLayoutCompact(cout, "  ");
}

class AriaMotionSensorPlayer : public RecordFormatStreamPlayer {
  bool onDataLayoutRead(const CurrentRecord& r, size_t blockIndex, DataLayout& dl) override {
    if (r.recordType == Record::Type::CONFIGURATION) {
      auto& config = getExpectedLayout<aria::MotionSensorConfigRecordMetadata>(dl, blockIndex);
      // Read config record metadata...
      printDataLayout(r, config);
    } else if (r.recordType == Record::Type::DATA) {
      auto& data = getExpectedLayout<aria::MotionSensorDataRecordMetadata>(dl, blockIndex);
      // Read data record metadata...
      printDataLayout(r, data);
    }
    return true;
  }
};

class AriaWifiBeaconPlayer : public RecordFormatStreamPlayer {
  bool onDataLayoutRead(const CurrentRecord& r, size_t blockIndex, DataLayout& dl) override {
    if (r.recordType == Record::Type::CONFIGURATION) {
      auto& config = getExpectedLayout<aria::WifiBeaconConfigRecordMetadata>(dl, blockIndex);
      // Read config record metadata...
      printDataLayout(r, config);
    } else if (r.recordType == Record::Type::DATA) {
      auto& data = getExpectedLayout<aria::WifiBeaconDataRecordMetadata>(dl, blockIndex);
      // Read data record metadata...
      printDataLayout(r, data);
    }
    return true;
  }
};

class AriaBluetoothBeaconPlayer : public RecordFormatStreamPlayer {
  bool onDataLayoutRead(const CurrentRecord& r, size_t blockIndex, DataLayout& dl) override {
    if (r.recordType == Record::Type::CONFIGURATION) {
      auto& config = getExpectedLayout<aria::BluetoothBeaconConfigRecordMetadata>(dl, blockIndex);
      // Read config record metadata...
      printDataLayout(r, config);
    } else if (r.recordType == Record::Type::DATA) {
      auto& data = getExpectedLayout<aria::BluetoothBeaconDataRecordMetadata>(dl, blockIndex);
      // Read data record metadata...
      printDataLayout(r, data);
    }
    return true;
  }
};

class AriaBarometerPlayer : public RecordFormatStreamPlayer {
  bool onDataLayoutRead(const CurrentRecord& r, size_t blockIndex, DataLayout& dl) override {
    if (r.recordType == Record::Type::CONFIGURATION) {
      auto& config = getExpectedLayout<aria::BarometerConfigRecordMetadata>(dl, blockIndex);
      // Read config record metadata...
      printDataLayout(r, config);
    } else if (r.recordType == Record::Type::DATA) {
      auto& data = getExpectedLayout<aria::BarometerDataRecordMetadata>(dl, blockIndex);
      // Read data record metadata...
      printDataLayout(r, data);
    }
    return true;
  }
};

void readIMU(RecordFileReader& reader, int index) {
  const StreamId id = reader.getStreamForType(RecordableTypeId::SlamImuData, index);
  auto player = make_unique<AriaMotionSensorPlayer>();
  if (id.isValid() && player)
    reader.setStreamPlayer(id, player.get());
  else
    fmt::print(stderr, "Could not read IMU index {}", index);
}

void readBLE(RecordFileReader& reader) {
  const StreamId id = reader.getStreamForType(RecordableTypeId::BluetoothBeaconRecordableClass);
  auto player = make_unique<AriaBluetoothBeaconPlayer>();
  if (id.isValid() && player)
    reader.setStreamPlayer(id, player.get());
  else
    fmt::print(stderr, "Could not read BLE");
}

void readMagnet(RecordFileReader& reader) {
  const StreamId id = reader.getStreamForType(RecordableTypeId::SlamMagnetometerData);
  auto player = make_unique<AriaMotionSensorPlayer>();
  if (id.isValid() && player)
    reader.setStreamPlayer(id, player.get());
  else
    fmt::print(stderr, "Could not read Magnetometer");
}

void readBarometer(RecordFileReader& reader) {
  const StreamId id = reader.getStreamForType(RecordableTypeId::BarometerRecordableClass);
  auto player = make_unique<AriaBarometerPlayer>();
  if (id.isValid() && player)
    reader.setStreamPlayer(id, player.get());
  else
    fmt::print(stderr, "Could not read Barometer");
}

void readWifi(RecordFileReader& reader) {
  const StreamId id = reader.getStreamForType(RecordableTypeId::WifiBeaconRecordableClass);
  auto player = make_unique<AriaWifiBeaconPlayer>();
  if (id.isValid() && player)
    reader.setStreamPlayer(id, player.get());
  else
    fmt::print(stderr, "Could not read Wifi");
}

void readVRSFile(string filePath) {
  RecordFileReader reader;
  if (reader.openFile(filePath) == 0) {
    fmt::print(stdout, "LOG: StreamReader for IMU 0");
    readIMU(reader, 0);
    fmt::print(stdout, "LOG: StreamReader for IMU 1");
    readIMU(reader, 1);
    fmt::print(stdout, "LOG: StreamReader for BLE");
    readBLE(reader);
    fmt::print(stdout, "LOG: StreamReader for Magnetometer");
    readMagnet(reader);
    fmt::print(stdout, "LOG: StreamReader for Barometer");
    readBarometer(reader);
    fmt::print(stdout, "LOG: StreamReader for Wifi");
    readWifi(reader);
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
