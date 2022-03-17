#include <fstream>
#include <string>
#include <vector>

#include <vrs/RecordFileReader.h>
#include <vrs/RecordFormatStreamPlayer.h>

#include <vrs/oss/aria/BarometerMetadata.h>
#include <vrs/oss/aria/BluetoothBeaconMetadata.h>
#include <vrs/oss/aria/MotionSensorMetadata.h>
#include <vrs/oss/aria/WifiBeaconMetadata.h>

using namespace std;
using namespace vrs;

namespace vivek_vrs_app {

class AriaMotionSensorPlayer : public RecordFormatStreamPlayer {
  ofstream csvFile;
  bool hasGyro, hasAcc, hasMag;
  fmt::memory_buffer buffer;
  string line;

  bool onDataLayoutRead(const CurrentRecord& r, size_t blockIndex, DataLayout& dl) override {
    if (r.recordType == Record::Type::CONFIGURATION) {
      auto& config = getExpectedLayout<aria::MotionSensorConfigRecordMetadata>(dl, blockIndex);
      buffer.clear();
      fmt::format_to(back_inserter(buffer), "timestamp,");
      if (config.hasAccelerometer.get()) {
        hasAcc = true;
        fmt::format_to(back_inserter(buffer), "accX,accY,accZ,");
      }
      if (config.hasGyroscope.get()) {
        hasGyro = true;
        fmt::format_to(back_inserter(buffer), "gyroX,gyroY,gyroZ,");
      }
      if (config.hasMagnetometer.get()) {
        hasMag = true;
        fmt::format_to(back_inserter(buffer), "magX,magY,magZ,");
      }
      line = to_string(buffer);
      line.pop_back();
      csvFile << line << "\n";
    } else if (r.recordType == Record::Type::DATA) {
      auto& data = getExpectedLayout<aria::MotionSensorDataRecordMetadata>(dl, blockIndex);
      buffer.clear();
      fmt::format_to(back_inserter(buffer), "{},", data.captureTimestampNs.get());
      if (hasAcc) {
        vector<float> accData;
        data.accelMSec2.get(accData);
        fmt::format_to(back_inserter(buffer), "{},{},{},", accData[0], accData[1], accData[2]);
      }
      if (hasGyro) {
        vector<float> gyroData;
        data.gyroRadSec.get(gyroData);
        fmt::format_to(back_inserter(buffer), "{},{},{},", gyroData[0], gyroData[1], gyroData[2]);
      }
      if (hasMag) {
        vector<float> magData;
        data.magTesla.get(magData);
        fmt::format_to(back_inserter(buffer), "{},{},{},", magData[0], magData[1], magData[2]);
      }
      line = to_string(buffer);
      line.pop_back();
      csvFile << line << "\n";
    }
    return true;
  }

 public:
  AriaMotionSensorPlayer(string filename)
      : RecordFormatStreamPlayer(),
        csvFile(),
        hasAcc(false),
        hasGyro(false),
        hasMag(false),
        buffer(),
        line() {
    csvFile.open(filename);
  }
};

class AriaWifiBeaconPlayer : public RecordFormatStreamPlayer {
  ofstream csvFile;
  fmt::memory_buffer buffer;

  bool onDataLayoutRead(const CurrentRecord& r, size_t blockIndex, DataLayout& dl) override {
    if (r.recordType == Record::Type::CONFIGURATION) {
      csvFile << "timestamp,ssid,bssid,freq,rssi\n";
    } else if (r.recordType == Record::Type::DATA) {
      auto& data = getExpectedLayout<aria::WifiBeaconDataRecordMetadata>(dl, blockIndex);
      buffer.clear();
      fmt::format_to(
          back_inserter(buffer),
          "{},{},{},{},{}\n",
          data.boardTimestampNs.get(),
          data.ssid.get(),
          data.bssidMac.get(),
          data.freqMhz.get(),
          data.rssi.get());
      csvFile << to_string(buffer);
    }
    return true;
  }

 public:
  AriaWifiBeaconPlayer(string filename) : RecordFormatStreamPlayer(), csvFile(), buffer() {
    csvFile.open(filename);
  }
};

class AriaBluetoothBeaconPlayer : public RecordFormatStreamPlayer {
  ofstream csvFile;
  fmt::memory_buffer buffer;

  bool onDataLayoutRead(const CurrentRecord& r, size_t blockIndex, DataLayout& dl) override {
    if (r.recordType == Record::Type::CONFIGURATION) {
      csvFile << "timestamp,id,rssi,freq\n";
    } else if (r.recordType == Record::Type::DATA) {
      auto& data = getExpectedLayout<aria::BluetoothBeaconDataRecordMetadata>(dl, blockIndex);
      buffer.clear();
      fmt::format_to(
          back_inserter(buffer),
          "{},{},{},{}\n",
          data.boardTimestampNs.get(),
          data.uniqueId.get(),
          data.rssi.get(),
          data.freqMhz.get());
      csvFile << to_string(buffer);
    }
    return true;
  }

 public:
  AriaBluetoothBeaconPlayer(string filename) : RecordFormatStreamPlayer(), csvFile(), buffer() {
    csvFile.open(filename);
  }
};

class AriaBarometerPlayer : public RecordFormatStreamPlayer {
  ofstream csvFile;
  fmt::memory_buffer buffer;

  bool onDataLayoutRead(const CurrentRecord& r, size_t blockIndex, DataLayout& dl) override {
    if (r.recordType == Record::Type::CONFIGURATION) {
      csvFile << "timestamp,pressure,altitude\n";
    } else if (r.recordType == Record::Type::DATA) {
      auto& data = getExpectedLayout<aria::BarometerDataRecordMetadata>(dl, blockIndex);
      buffer.clear();
      fmt::format_to(
          back_inserter(buffer),
          "{},{},{}\n",
          data.captureTimestampNs.get(),
          data.pressure.get(),
          data.altitude.get());
      csvFile << to_string(buffer);
    }
    return true;
  }

 public:
  AriaBarometerPlayer(string filename) : RecordFormatStreamPlayer(), csvFile(), buffer() {
    csvFile.open(filename);
  }
};

struct VRSReader {
  /// This function is the entry point for your reader
  static void readFile(const string& vrsFilePath) {
    RecordFileReader reader;
    string exp = vrsFilePath.substr(0, vrsFilePath.length() - 4); // remove .vrs extension
    int status = reader.openFile(vrsFilePath);
    if (status == SUCCESS) {
      vector<unique_ptr<StreamPlayer>> streamPlayers;
      // Map the devices referenced in the file to stream player objects
      // Just ignore the device(s) you do not care for
      for (auto id : reader.getStreams()) {
        unique_ptr<StreamPlayer> streamPlayer;
        switch (id.getTypeId()) {
          case RecordableTypeId::SlamImuData:
            streamPlayer = make_unique<AriaMotionSensorPlayer>(
                fmt::format("{}_IMU_{}.csv", exp, id.getInstanceId()));
            break;
          case RecordableTypeId::SlamMagnetometerData:
            streamPlayer = make_unique<AriaMotionSensorPlayer>(
                fmt::format("{}_Magnet_{}.csv", exp, id.getInstanceId()));
            break;
          case RecordableTypeId::WifiBeaconRecordableClass:
            streamPlayer = make_unique<AriaWifiBeaconPlayer>(
                fmt::format("{}_Wifi_{}.csv", exp, id.getInstanceId()));
            break;
          case RecordableTypeId::BluetoothBeaconRecordableClass:
            streamPlayer = make_unique<AriaBluetoothBeaconPlayer>(
                fmt::format("{}_BLE_{}.csv", exp, id.getInstanceId()));
            break;
          case RecordableTypeId::BarometerRecordableClass:
            streamPlayer = make_unique<AriaBarometerPlayer>(
                fmt::format("{}_Baro_{}.csv", exp, id.getInstanceId()));
            break;
          default:
            break;
        }
        if (streamPlayer) {
          reader.setStreamPlayer(id, streamPlayer.get());
          streamPlayers.emplace_back(move(streamPlayer));
        }
      }
      if (!streamPlayers.empty()) {
        fmt::print("Processing {} streams.\n", streamPlayers.size(), vrsFilePath);
        reader.readAllRecords();
      }
    } else {
      fmt::print(stderr, "Failed to open '{}', {}.\n", vrsFilePath, errorCodeToMessage(status));
    }
  }
};

} // namespace vivek_vrs_app

int main(int argc, char** argv) {
  for (int i = 1; i < argc; ++i) {
    vivek_vrs_app::VRSReader::readFile(argv[i]);
  }
  return 0;
}
