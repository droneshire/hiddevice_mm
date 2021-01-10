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

def monitor_mute_me(verbose=False):
    last_button_status = False
    audio = OsAudio(verbose=verbose)
    if verbose:
        print(audio.get_mics())
    audio.set_mic(2)
    while True:
        button_status = mm.get_button_status()
        if last_button_status != button_status:
            print("toggling mute!")
            if audio.is_muted():
                audio.unmute()
            else:
                audio.mute()
        last_button_status = button_status
        time.sleep(0.2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true", help="lots of verbose printing")
    args = parser.parse_args()

    mm = MuteMeHid(verbose=args.verbose)
    mm.open()

    run_event = threading.Event()
    run_event.set()

    def thread_wrapper(mute_me, run_event):
        mute_me.receive_thread(run_event)

    thread = threading.Thread(target=thread_wrapper, args=(mm, run_event))
    thread.start()

    try:
        monitor_mute_me(args.verbose)
    except KeyboardInterrupt as exception:
        pass
    except Exception as exception:
        # stop the thread
        run_event.clear()
        thread.join()
        mm.close()
        raise exception

    # stop the thread
    run_event.clear()
    thread.join()

    mm.close()
