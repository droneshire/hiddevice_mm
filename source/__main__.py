import argparse
import time
import threading
import sys

from mm_driver import MuteMeHid

if sys.platform == "linux" or sys.platform == "linux2":
    from audio.linux_audio import LinuxAudio as OsAudio
elif sys.platform == "darwin":
    # TODO(ross): OS X
    from audio.mac_audio import MacAudio as OsAudio
elif sys.platform == "win32":
    # TODO(ross): Windows
    from audio.windows_audio import WindowsAudio as OsAudio


def monitor_muteme(muteme_driver, verbose=False):
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true", help="lots of verbose printing")
    args = parser.parse_args()

    muteme_driver = MuteMeHid(verbose=args.verbose)
    muteme_driver.open()

    run_event = threading.Event()
    run_event.set()

    def thread_wrapper(mm, run_event):
        mm.receive_thread(run_event)

    thread = threading.Thread(target=thread_wrapper, args=(muteme_driver, run_event))
    thread.start()

    def cleanup():
        # stop the HID thread
        run_event.clear()
        thread.join()
        # close the device
        muteme_driver.close()

    try:
        monitor_muteme(muteme_driver, args.verbose)
    except KeyboardInterrupt as exception:
        pass
    except Exception as exception:
        cleanup()
        raise exception
    cleanup()
