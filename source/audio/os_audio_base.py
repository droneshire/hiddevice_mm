""" Base class for audio representation of the OS """


class OsAudioBase(object):
    def is_muted(self):
        raise NotImplementedError

    def mute(self):
        raise NotImplementedError

    def unmute(self):
        raise NotImplementedError

    def get_mics(self):
        raise NotImplementedError

    def set_mic(self, mic_index):
        raise NotImplementedError
