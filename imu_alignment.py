import csv
import os
import sys
from pathlib import Path
from typing import Callable, List, Tuple

import matplotlib
import numpy as np
from PyQt5 import QtCore, QtWidgets

matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigCanvas
from matplotlib.backends.backend_qt5agg import \
    NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class Canvas(FigCanvas):
    def __init__(self, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)


class AlignmentWindow(QtWidgets.QMainWindow):
    def __init__(self, matches: List[Tuple[str, str]], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.canvas = Canvas()
        self.phone_axis = 1
        self.aria_axis = 1
        self.db_offset = 0
        self.aria_offset = 0
        self.phone_imu_data = None
        self.aria_imu_data = None

        self.create_main_panel()
        self.draw_figure()
        self.show()
        self.idx = 0
        self.matches = matches
        process(self, self.matches[self.idx])

    def closeEvent(self, event):
        global idx, matches
        if self.idx < len(matches) - 1:
            print(self.db_offset, self.aria_offset)
            self.idx += 1
            process(self, self.matches[self.idx])
            event.ignore()
        else:
            print(self.db_offset, self.aria_offset)
            event.accept()

    def set_data(self, phone_imu_data, aria_imu_data):
        self.phone_imu_data = phone_imu_data
        self.aria_imu_data = aria_imu_data
        self.draw_figure()

    def create_main_panel(self):

        widget = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout()
        widget.setLayout(vbox)
        self.setCentralWidget(widget)

        toolbar = NavigationToolbar(self.canvas, self)

        vbox.addWidget(toolbar)
        vbox.addWidget(self.canvas)

        wbox_imus = QtWidgets.QHBoxLayout()
        vbox_db = QtWidgets.QVBoxLayout()
        db_group = QtWidgets.QButtonGroup(widget)
        db_accX_btn = QtWidgets.QRadioButton("AccX")
        db_accX_btn.setChecked(True)
        db_accX_btn.toggled.connect(lambda: self.replot_phone(db_accX_btn, 1))
        db_accY_btn = QtWidgets.QRadioButton("AccY")
        db_accY_btn.toggled.connect(lambda: self.replot_phone(db_accY_btn, 2))
        db_accZ_btn = QtWidgets.QRadioButton("AccZ")
        db_accZ_btn.toggled.connect(lambda: self.replot_phone(db_accZ_btn, 3))
        db_group.addButton(db_accX_btn)
        db_group.addButton(db_accY_btn)
        db_group.addButton(db_accZ_btn)
        db_radiogroup = QtWidgets.QHBoxLayout()
        db_radiogroup.addWidget(db_accX_btn)
        db_radiogroup.addWidget(db_accY_btn)
        db_radiogroup.addWidget(db_accZ_btn)
        db_radiogroup.addStretch(1)
        vbox_db.addWidget(QtWidgets.QLabel("Phone"))
        vbox_db.addLayout(db_radiogroup)
        db_offset = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        db_offset.setMinimum(0)
        db_offset.setMaximum(100)
        db_offset.setValue(0)
        db_offset.setTickInterval(1)
        db_offset.valueChanged.connect(
            lambda: self.db_offset_changed(db_offset.value())
        )
        vbox_db.addWidget(db_offset)
        vbox_aria = QtWidgets.QVBoxLayout()
        aria_group = QtWidgets.QButtonGroup(widget)
        aria_accX_btn = QtWidgets.QRadioButton("AccX")
        aria_accX_btn.setChecked(True)
        aria_accX_btn.toggled.connect(lambda: self.replot_aria(aria_accX_btn, 1))
        aria_accY_btn = QtWidgets.QRadioButton("AccY")
        aria_accY_btn.toggled.connect(lambda: self.replot_aria(aria_accY_btn, 2))
        aria_accZ_btn = QtWidgets.QRadioButton("AccZ")
        aria_accZ_btn.toggled.connect(lambda: self.replot_aria(aria_accZ_btn, 3))
        aria_group.addButton(aria_accX_btn)
        aria_group.addButton(aria_accY_btn)
        aria_group.addButton(aria_accZ_btn)
        aria_radiogroup = QtWidgets.QHBoxLayout()
        aria_radiogroup.addWidget(aria_accX_btn)
        aria_radiogroup.addWidget(aria_accY_btn)
        aria_radiogroup.addWidget(aria_accZ_btn)
        aria_radiogroup.addStretch(1)
        vbox_aria.addWidget(QtWidgets.QLabel("Aria"))
        vbox_aria.addLayout(aria_radiogroup)
        aria_offset = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        aria_offset.setMinimum(0)
        aria_offset.setMaximum(100)
        aria_offset.setValue(0)
        aria_offset.setTickInterval(1)
        aria_offset.valueChanged.connect(
            lambda: self.aria_offset_changed(aria_offset.value())
        )
        vbox_aria.addWidget(aria_offset)
        wbox_imus.addLayout(vbox_db)
        wbox_imus.addLayout(vbox_aria)

        vbox.addLayout(wbox_imus)

    def db_offset_changed(self, value):
        self.db_offset = value
        self.draw_figure()

    def aria_offset_changed(self, value):
        self.aria_offset = value
        self.draw_figure()

    def replot_aria(self, btn, aria_axis):
        if btn.isChecked() == True:
            self.aria_axis = aria_axis
            self.draw_figure()

    def replot_phone(self, btn, phone_axis):
        if btn.isChecked() == True:
            self.phone_axis = phone_axis
            self.draw_figure()

    def draw_figure(self):
        if self.phone_imu_data is not None and self.aria_imu_data is not None:
            self.canvas.axes.clear()
            self.canvas.axes.plot(
                self.phone_imu_data[:, 0] + self.db_offset,
                self.phone_imu_data[:, self.phone_axis],
            )
            self.canvas.axes.plot(
                self.aria_imu_data[:, 0] + self.aria_offset,
                self.aria_imu_data[:, self.aria_axis],
            )
            self.canvas.draw()


def match(file: Path, against_files: List[Path]) -> Path:
    """Finds the best match (based on timestamp) of the file against the list of files"""
    start_time = float(csv.DictReader(open(file, "r")).__next__()["timestamp"])
    against_times = [
        float(csv.DictReader(open(aFile, "r")).__next__()["realtime"]) / 1e9
        for aFile in against_files
    ]
    against_diffs = [(at - start_time) ** 2 for at in against_times]
    print("TError:", np.min(against_diffs))
    return against_files[np.argmin(against_diffs)]


def dir_match(dir: Path) -> List[Tuple[str, str]]:
    assert os.path.isdir(dir)
    files = os.listdir(dir)
    db_imu_files = list(
        map(
            lambda db: Path(dir / (db + "_imu.csv")),
            filter(lambda path: path.endswith(".db"), files),
        )
    )
    vrs_time_files = list(
        map(
            lambda vrs: Path(dir / (vrs[:-4] + "_Time_1.csv")),
            filter(lambda path: path.endswith(".vrs"), files),
        )
    )
    matches: List[Tuple[str, str]] = []
    for imu_file in db_imu_files:
        vrs_file = match(imu_file, vrs_time_files)
        matches.append((str(imu_file)[:-8], str(vrs_file)[:-11]))
        vrs_time_files.remove(vrs_file)
    return matches


def process(window: AlignmentWindow, match: Tuple[str, str]):
    time_map_reader = csv.DictReader(open(match[1] + "_Time_1.csv", "r"))
    time_map_0, time_map_1 = time_map_reader.__next__(), time_map_reader.__next__()
    time_map_scale = (float(time_map_1["realtime"]) - float(time_map_0["realtime"])) / (
        float(time_map_1["timestamp"]) - float(time_map_0["timestamp"])
    )
    time_map_offset = float(time_map_0["realtime"]) - time_map_scale * float(
        time_map_0["timestamp"]
    )
    peak_align(
        window,
        Path(match[0] + "_imu.csv"),
        Path(match[1] + "_IMU_1.csv"),
        lambda x: time_map_scale * x + time_map_offset,
    )


def peak_align(
    window: AlignmentWindow,
    db_imu: Path,
    aria_imu: Path,
    time_map: Callable[[float], float],
):
    db_data = csv.DictReader(open(db_imu, "r"))
    aria_data = csv.DictReader(open(aria_imu, "r"))
    db_time, db_accx, db_accy, db_accz = [], [], [], []
    for row in db_data:
        db_time.append(float(row["timestamp"]))
        db_accx.append(float(row["accX"]))
        db_accy.append(float(row["accY"]))
        db_accz.append(float(row["accZ"]))
    db_imu_data = np.stack(list(map(np.array, (db_time, db_accx, db_accy, db_accz))), 1)
    db_imu_data[:, 1:] *= -9.8

    aria_time, aria_accx, aria_accy, aria_accz = [], [], [], []
    for row in aria_data:
        aria_time.append(time_map(float(row["timestamp"])))
        aria_accx.append(float(row["accX"]))
        aria_accy.append(float(row["accY"]))
        aria_accz.append(float(row["accZ"]))
    aria_imu_data = np.stack(
        list(map(np.array, (aria_time, aria_accx, aria_accy, aria_accz))), 1
    )
    aria_imu_data[:, 0] /= 1e9
    window.set_data(db_imu_data, aria_imu_data)


if __name__ == "__main__":
    for dir in sys.argv[1:]:
        matches = dir_match(Path(dir).resolve())
        assert len(matches) > 0
        app = QtWidgets.QApplication([])
        w = AlignmentWindow(matches)
        app.exec_()
