import sys
from PyQt5.QtWidgets import QApplication, QMainWindow

from mm_driver import MuteMeHid

if sys.platform == "linux" or sys.platform == "linux2":
    from audio.linux_audio import LinuxAudio as OsAudio
elif sys.platform == "darwin":
    # TODO(ross): OS X
    from audio.mac_audio import MacAudio as OsAudio
elif sys.platform == "win32":
    # TODO(ross): Windows
    from audio.windows_audio import WindowsAudio as OsAudio


class MuteMeUi(QMainWindow):
    def __init__(self):
        super().__init__()
        self.audio = OsAudio()
        self.mute_me = MuteMeHid(verbose=True)

        self.setGeometry(300, 300, 600, 400)
        self.setWindowTitle("PyQt5 window")
        self.show()


def ui_begin():
    app = QApplication(sys.argv)
    window = MuteMeUi()
    sys.exit(app.exec_())
