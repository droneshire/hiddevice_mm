""" HID wrapper for the MuteMe device """
import hid
import threading
import time
import struct

from enum import Enum


class Led(Enum):
    kNone = 0
    kRed = 1
    kGreen = 2
    kRedGreenFlash = 3
    kBlue = 4
    kRedBlueFlash = 5
    kGreenBlueFlash = 6
    kRedGreenBlueFlash = 7
    kYellow = 8
    kRedYellowFlash = 9
    kOff = 44


class Report(Enum):
    kModifierKeys = 0
    kReserved = 1
    kKeypress1 = 2
    kKeypress2 = 3
    kKeypress3 = 4
    kKeypress4 = 5
    kKeypress5 = 6
    kKeypress6 = 7


VENDOR_ID = 0x16C0
PRODUCT_ID = 0x27DB
REPORT_LENGTH = 8
INVALID_BUTTON_INPUTS = [0]
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

            button_val = raw_report[MUTEME_BUTTON.value]
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
        self._write_output_report(Led.kRed)

    def set_unmuted(self):
        self._write_output_report(Led.kGreen)

    def set_idle(self):
        self._write_output_report(Led.kOff)

    def _read_input_report(self, timeout):
        """
        8 byte input report:
         b7       | b6       | b5       | b4       | b3       | b2       | b1     | b0
        Key Code 6|Key Code 5|Key Code 4|Key Code 3|Key Code 2|Key Code 1|Reserved|Modifier Keys|
        """
        data = []
        try:
            data = self.device.read(8, timeout)
        except IOError as e:
            print("Error reading response: {}".format(e))
        return data

    def _write_output_report(self, led_color):
        """
        output report is a one byte command that has 8 bits of resolution.
        color command represented in the Led class
        """
        bytes_sent = 0
        try:
            bytes_sent = self.device.write([led_color.value])
        except IOError as e:
            print("Error reading response: {}".format(e))
        return bytes_sent
