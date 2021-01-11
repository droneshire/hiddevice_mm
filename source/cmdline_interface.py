import sys

if sys.platform == "linux" or sys.platform == "linux2":
    from audio.linux_audio import LinuxAudio as OsAudio
elif sys.platform == "darwin":
    # TODO(ross): OS X
    from audio.mac_audio import MacAudio as OsAudio
elif sys.platform == "win32":
    # TODO(ross): Windows
    from audio.windows_audio import WindowsAudio as OsAudio

def muteme_commandline(muteme_driver, verbose=False):
    last_button_status = False
    audio = OsAudio(verbose=verbose)
    if verbose:
        print(audio.get_mics())
    audio.set_mic(2)
    while True:
        button_status = muteme_driver.get_button_status()
        if last_button_status != button_status:
            if verbose:
                print("toggling mute!")
            if audio.is_muted():
                audio.unmute()
                muteme_driver.set_unmuted()
            else:
                audio.mute()
                muteme_driver.set_muted()
        last_button_status = button_status
        time.sleep(0.2)
