import os
import sys

from PySide2.QtCore import Slot, Qt, QTimer
from PySide2.QtGui import QIcon
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import QApplication
from PySide2.QtWidgets import QComboBox
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QPushButton
from PySide2.QtWidgets import QSystemTrayIcon
from PySide2.QtWidgets import QVBoxLayout
from PySide2.QtWidgets import QWidget

if sys.platform == "linux" or sys.platform == "linux2":
    from audio.linux_audio import LinuxAudio as OsAudio
elif sys.platform == "darwin":
    # TODO(ross): OS X
    from audio.mac_audio import MacAudio as OsAudio
elif sys.platform == "win32":
    # TODO(ross): Windows
    from audio.windows_audio import WindowsAudio as OsAudio


class MuteMeUi(QWidget):
    def __init__(self, muteme_driver, update_rate, verbose=False):
        QWidget.__init__(self)

        self.muteme_driver = muteme_driver
        self.audio = OsAudio(verbose=verbose)
        self.verbose = verbose
        self.last_button_status = False

        self.available_mics = self.audio.get_mics()
        self.audio.set_mic(0)

        # timer for checking on muteme status
        self.timer = QTimer()
        self.timer.setInterval(update_rate)
        self.timer.start()

        # combo box for mic select
        self.mic_combo_box = QComboBox()
        self.mic_combo_box.addItems(self.available_mics)
        self.mic_combo_box.setCurrentIndex(0)

        # create toggle button
        self.last_button_status = False
        muteme_button_text = "Unmute" if self.audio.is_muted() else "Mute"
        self.muteme_button = QPushButton(muteme_button_text)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.mic_combo_box)
        self.layout.addWidget(self.muteme_button)
        self.setLayout(self.layout)

        # Button signal
        self.muteme_button.clicked.connect(self._handle_muteme_button_click)
        # Timer signal
        self.timer.timeout.connect(self._handle_timer)
        # Combo box signal
        self.mic_combo_box.currentIndexChanged.connect(self._handle_change_mic)

        self.setWindowTitle("MuteMe App")

    def closeEvent(self, event):
        if self.verbose:
            print("closing ui")
        event.accept()

    def _toggle_muteme(self):
        is_muted = self.audio.is_muted()
        if is_muted:
            self.audio.unmute()
            self.muteme_driver.set_unmuted()
        else:
            self.audio.mute()
            self.muteme_driver.set_muted()

        if self.verbose:
            print("Muting!" if not is_muted else "Unmuting!")
        return not is_muted

    def _handle_timer(self):
        button_status = self.muteme_driver.get_button_status()
        if button_status == self.last_button_status:
            return

        is_muted = self._toggle_muteme()

        self.muteme_button.setText("Unmute" if is_muted else "Mute")
        self.last_button_status = button_status

    @Slot(int)
    def _handle_change_mic(self, index):
        mic = self.mic_combo_box.itemIcon(index)
        if self.verbose:
            print("Selecting {}".format(mic))
        self.audio.set_mic(index)

    @Slot()
    def _handle_muteme_button_click(self):
        is_muted = self._toggle_muteme()
        self.muteme_button.setText("Unmute" if is_muted else "Mute")


def muteme_ui(muteme_driver, update_rate, verbose=False):
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    widget = MuteMeUi(muteme_driver, update_rate, verbose)
    widget.resize(200, 50)
    widget.show()

    app.exec_()
