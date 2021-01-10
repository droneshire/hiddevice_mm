""" HID wrapper for the MuteMe device """
import hid
import threading
import time
import struct

from enum import Enum

VENDOR_ID = 0x16c0
PRODUCT_ID = 0x27db
REPORT_LENGTH = 8
INVALID_BUTTON_INPUTS = [0]

class Led(Enum):
    kRed = 0,
    kGreen = 1,

class Report(Enum):
    kModifierKeys = 0,
    kReserved = 1,
    kKeypress1 = 2,
    kKeypress2 = 3,
    kKeypress3 = 4,
    kKeypress4 = 5,
    kKeypress5 = 6,
    kKeypress6 = 7,

    def val(self):
        return self.value[0]


MUTEME_BUTTON = Report.kKeypress2

class MuteMeHid(object):

    def __init__(self, verbose=False):
        self.log_name = "MuteMeHid: "
        self.device = hid.device()
        self.verbose = verbose

        self.button_status = 0

        self.lock = threading.Lock()
        self.toggle = False

    def open(self):
        try:
            self.device.open(VENDOR_ID, PRODUCT_ID)
            if self.verbose:
                print("Opened {:04x}:{:04x}".format(VENDOR_ID, PRODUCT_ID))
        except IOError:
            if self.verbose:
                print("Failed to open {:04x}:{:04x}".format(VENDOR_ID, PRODUCT_ID))

    def close(self):
        try:
            self.device.close()
            if self.verbose:
                print("Closed {:04x}:{:04x}".format(VENDOR_ID, PRODUCT_ID))
        except:
            if self.verbose:
                print("Failed to close {:04x}:{:04x}".format(VENDOR_ID, PRODUCT_ID))

    def receive_thread(self, run_event, update_rate=0.01):
        # thread that simply just listens for new input reports
        report_stream = []

        while run_event.is_set():
            raw_report = self._read_input_report(timeout=500)

            if len(raw_report) != REPORT_LENGTH:
                continue

            button_val = raw_report[MUTEME_BUTTON.val()]
            if button_val in INVALID_BUTTON_INPUTS:
                continue

            if self.verbose and raw_report:
                print(raw_report)

            if button_val == self.button_status:
                continue

            if self.verbose:
                print("MuteMe pressed")
            self.button_status = button_val
            report_stream = []

            self.lock.acquire()
            self.toggle = not self.toggle
            self.lock.release()


    def get_button_status(self):
        self.lock.acquire()
        button_status = self.toggle
        self.lock.release()
        return button_status

    def set_muted(self):
        self._write_output_report(Led.kGreen)

    def set_unmuted(self):
        self._write_output_report(Led.kGreen)

    def _read_input_report(self, timeout):
        return self.device.read(8, timeout)

    def _write_output_report(self, led_color):
        # TODO(ross): implementonce you know the structure
        pass