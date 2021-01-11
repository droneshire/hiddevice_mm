""" Linux implementation of interfacing with microphones"""

import re
import subprocess

from audio.os_audio_base import OsAudioBase
from utils import is_zoom_running

# interact with audio using amixer or pulseaudio
USE_AMIXER = False


class LinuxMic(object):
    """ Simple wrapper class for linux mic features """

    def __init__(self, mic_inx, mic_name, mic_control_name):
        self.card_inx = mic_inx
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

        # still update the system after updating zoom, so that we track state
        self._maybe_send_zoom_mute_toggle()

        mic = self.available_mics[self.mic_inx]

        if USE_AMIXER:
            cmd = ["amixer", "-c", str(mic.card_inx), "cset", mic.mic_control_name, "0"]
        else:
            cmd = ["pactl", "set-source-mute", mic.mic_control_name, "1"]
        self._run_cmd(cmd)

    def unmute(self):
        if not self.available_mics:
            if self.verbose:
                print("no mic selected!")
            return

        # still update the system after updating zoom, so that we track state
        self._maybe_send_zoom_mute_toggle()

        mic = self.available_mics[self.mic_inx]

        if USE_AMIXER:
            cmd = ["amixer", "-c", str(mic.card_inx), "cset", mic.mic_control_name, "1"]
        else:
            cmd = ["pactl", "set-source-mute", mic.mic_control_name, "0"]
        self._run_cmd(cmd)

    def get_mics(self):
        self._update_available_mics()
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
        output = ""
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

    def _maybe_send_zoom_mute_toggle(self):
        if not is_zoom_running():
            return False
        cmd = [
            "xdotool",
            "search",
            "--name",
            "Zoom Meeting",
            "windowactivate",
            "--sync",
            "%1",
            "key",
            "alt+a",  # toggle zoom
            "windowactivate",
            "$(xdotool getactivewindow)",
        ]
        self._run_cmd(cmd)
        return True

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

    def _update_available_mics(self):
        if USE_AMIXER:
            self._parse_amixer_contents()
        else:
            self._parse_pactl_sources()

    def _is_mic_muted(self):
        return self._amixer_is_muted() if USE_AMIXER else self._pacmd_is_muted()

    def _parse_amixer_contents(self):
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
                self.available_mics.append(LinuxMic(card[0], control_name, cset_name))

    def _amixer_is_muted(self):
        """ Parses amixer output for mute switch status

        Example output:
        #: amixer -c 0 cset iface=MIXER,name='Headset Mic Playback Switch'
        numid=7,iface=MIXER,name='Headset Mic Playback Switch'
            ; type=BOOLEAN,access=rw------,values=2
            : values=on,on
        """
        mic = self.available_mics[self.mic_inx]
        cmd = ["amixer", "-c", str(mic.card_inx), "cset", mic.mic_control_name]
        return "off" in self._run_cmd(cmd).split("values=")[2]

    def _pactl_get_mic_stats(self):
        """
        Example Output:
        ]$ pactl list sources
        Source #0
            State: RUNNING
            Name: alsa_input.usb-Sonix_Technology_Co.__Ltd._USB_2.0_Camera_SN0001-02.analog-mono
            Description: USB 2.0 Camera Analog Mono
            ....
        Source #1
            State: IDLE
            Name: alsa_output.pci-0000_00_1f.3.hdmi-stereo.monitor
            Description: Monitor of Built-in Audio Digital Stereo (HDMI)
            ...
        Source #2
            State: IDLE
            Name: alsa_input.pci-0000_00_1f.3.analog-stereo
            Description: Built-in Audio Analog Stereo
            ...
        """
        cmd = ["pactl", "list", "sources"]
        output = self._run_cmd(cmd)
        sources_raw = output.split("Source #")[1:]
        sources = []
        for source in sources_raw:
            source_stats = dict(l.strip().split(":", 1) for l in source.splitlines() if ":" in l)
            sources.append(source_stats)
        return sources

    def _parse_pactl_sources(self):
        for index, mic in enumerate(self._pactl_get_mic_stats()):
            mic_name = mic.get("Description", "").strip()
            mic_control_name = mic.get("Name", "").strip()
            self.available_mics.append(LinuxMic(index, mic_name, mic_control_name))

    def _pactl_get_system_mic_stats(self):
        for mic in self._pactl_get_mic_stats():
            if mic["State"].strip() == "RUNNING":
                return mic
        return {}

    def _pacmd_is_muted(self):
        mic_status = self._pactl_get_mic_stats()[self.mic_inx]
        return mic_status["Mute"].strip() == "yes"
