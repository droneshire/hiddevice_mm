""" Linux implementation of interfacing with microphones"""

import re
import subprocess

from audio.mic_audio import OsAudioBase

class AmixerMic(object):
    """ Simple wrapper class for amixer mic features """
    def __init__(self, card_inx, mic_name, mic_control_name):
        self.card_inx = card_inx
        self.mic_name = mic_name
        self.mic_control_name = mic_control_name

class LinuxAudio(OsAudioBase):

    def __init__(self, verbose=False):
        super(LinuxAudio, self).__init__()
        self.verbose = verbose

        # corresponds to the asound cards
        self.available_mics = []
        self.mic_inx = 0

    def is_muted(self):
        if not self.available_mics:
            if self.verbose:
                print("no mic selected!")
            return False
        return self._is_mic_muted()

    def mute(self):
        if not self.available_mics:
            if self.verbose:
                print("no mic selected!")
            return
        mic = self.available_mics[self.mic_inx]
        cmd = ["amixer", "-c", str(mic.card_inx), "cset", mic.mic_control_name, "0"]
        self._run_cmd(cmd)


    def unmute(self):
        if not self.available_mics:
            if self.verbose:
                print("no mic selected!")
            return

        mic = self.available_mics[self.mic_inx]
        cmd = ["amixer", "-c", str(mic.card_inx), "cset", mic.mic_control_name, "1"]
        self._run_cmd(cmd)

    def get_mics(self):
        self._get_available_mics()
        return [m.mic_name for m in self.available_mics]

    def set_mic(self, mic_index):
        if not self.available_mics or mic_index >= len(self.available_mics):
            if self.verbose:
                print("failed to set mic")
            return
        if self.verbose:
            print("Choosing {}".format(self.available_mics[mic_index].mic_name))
        self.mic_inx = mic_index

    def _run_cmd(self, cmd, err_msg=None):
        if not isinstance(cmd, list):
            return ""
        try:
            output = subprocess.check_output(cmd)
            if not isinstance(output, str):
                output = output.decode()
            if self.verbose:
                print("calling: {}".format(cmd))
        except subprocess.CalledProcessError:
            if self.verbose:
                print("failed to run {}".format(cmd) if err_msg is None else err_msg)
        return output

    def _get_available_acards(self):
        """ Finds the audio cards on the device using /proc/asound/cards.

        Example output:
         0 [PCH            ]: HDA-Intel - HDA Intel PCH
                      HDA Intel PCH at 0xddd28000 irq 143
         2 [Camera         ]: USB-Audio - USB 2.0 Camera
                      Sonix Technology Co., Ltd. USB 2.0 Camera at usb-0000:00:14.0-2.3.5, high speed
        """
        SOUNDCARD_PROCFS_PATH = "/proc/asound/cards"
        SOUNDCARD_PROCFS_REGEX = re.compile(r"^\s+(\d+)\s+\[(.*)\]\:.*$")

        cards = []
        with open(SOUNDCARD_PROCFS_PATH, "r") as infile:
            soundcard_info = infile.readlines()
            for line in soundcard_info:
                match = SOUNDCARD_PROCFS_REGEX.match(line)
                if not match:
                    continue
                card_inx = int(match.group(1))
                card_name = match.group(2).strip()
                cards.append((card_inx, card_name))
                if self.verbose:
                    print("Found card index {}".format(card_inx))
        return cards

    def _get_available_mics(self):
        """ Parse the amixer contents output for each card and determine if
        there is a mic switch control
        Example output:

        #: amixer -c 2 contents
        numid=4,iface=CARD,name='Keep Interface'
        ; type=BOOLEAN,access=rw------,values=1
        : values=off
        numid=2,iface=MIXER,name='Mic Capture Switch'
        ; type=BOOLEAN,access=rw------,values=1
        : values=off
        numid=3,iface=MIXER,name='Mic Capture Volume'
        ; type=INTEGER,access=rw---R--,values=1,min=0,max=256,step=0
        : values=61
        | dBminmax-min=-95.00dB,max=0.00dB
        numid=1,iface=PCM,name='Capture Channel Map'
        ; type=INTEGER,access=r----R--,values=1,min=0,max=36,step=0
        : values=2
        | container
            | chmap-fixed=MONO
        """
        available_cards = self._get_available_acards()
        self.available_mics = []
        for card in available_cards:
            cmd = ["amixer", "-c", str(card[0]), "contents"]
            controls = self._run_cmd(cmd).split("numid=")
            for control in controls:
                if "Mic" not in control:
                     continue
                if "type=BOOLEAN" not in control:
                    continue
                if "Phantom" in control:
                    continue
                if "access=rw" not in control:
                    continue
                control_lines = control.splitlines()
                control_name = control_lines[0].split("name=", 1)[1]
                cset_name = control_lines[0].split(",", 1)[1]
                self.available_mics.append(AmixerMic(card[0], control_name, cset_name))

    def _is_mic_muted(self):
        """ Parses amixer output for mute switch status

        Example output:
        #: amixer -c 0 cset iface=MIXER,name='Headset Mic Playback Switch'
        numid=7,iface=MIXER,name='Headset Mic Playback Switch'
            ; type=BOOLEAN,access=rw------,values=2
            : values=on,on
        """
        is_muted = False
        mic = self.available_mics[self.mic_inx]
        cmd = ["amixer", "-c", str(mic.card_inx), "cset", mic.mic_control_name]
        return "off" in self._run_cmd(cmd).split("values=")[2]
