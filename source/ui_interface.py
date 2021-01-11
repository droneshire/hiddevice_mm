import sys

from PySide2.QtCore import Slot, Qt
from PySide2.QtGui import QIcon
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import QApplication
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QPushButton
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
    def __init__(self, muteme_driver, verbose=False):
        QWidget.__init__(self)

        self.muteme_driver = muteme_driver
        self.audio = OsAudio(verbose=verbose)
        self.verbose = verbose

        # TODO(ross): make this a select
        self.audio.get_mics()
        self.audio.set_mic(2)

        self.setWindowTitle("MuteMe App")

        # images
        self.mute_img = QPixmap("../icons/mute.png")
        self.unmute_img = QPixmap("../icons/unmute.png")
        image_label = QLabel(self)
        pixmap = self.mute_img if self.audio.is_muted() else self.unmute_img
        image_label.setPixmap(pixmap)
        image_label.setScaledContents(True)
        self.resize(pixmap.width(), pixmap.height())

        # create toggle button
        self.last_button_status = False
        muteme_button_text = "Unmute" if self.audio.is_muted() else "Mute"
        self.muteme_button = QPushButton(muteme_button_text)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.muteme_button)
        self.setLayout(self.layout)

        # Button signal
        self.muteme_button.clicked.connect(self.handle_muteme_button_click)

    def closeEvent(self, event):
        if self.verbose:
            print("closing ui")
        event.accept()

    @Slot()
    def handle_muteme_button_click(self):
        is_muted = self.audio.is_muted()
        if is_muted:
            self.audio.unmute()
            self.muteme_driver.set_unmuted()
            image = self.unmute_img
        else:
            self.audio.mute()
            self.muteme_driver.set_muted()
            image = self.mute_img

        if self.verbose:
            print("Muting!" if not is_muted else "Unmuting!")


        self.last_button_status = self.muteme_driver.get_button_status()
        muteme_button_text = "Unmute" if self.audio.is_muted() else "Mute"
        self.muteme_button.setText(muteme_button_text)

def muteme_ui(muteme_driver, verbose=False):
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    widget = MuteMeUi(muteme_driver, verbose)
    widget.resize(200, 200)
    widget.show()

    app.exec_()
