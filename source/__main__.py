import argparse
import time
import threading

from cmdline_interface import muteme_commandline
from mm_driver import MuteMeHid
from ui_interface import muteme_ui


def muteme_main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true", help="lots of verbose printing")
    parser.add_argument("--cmdline", action="store_true", help="commandline version only")
    parser.add_argument(
        "--update-rate", type=float, default=0.5, help="poll rate for muteme button"
    )
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
        # set the color to idle mode?
        muteme_driver.set_idle()
        # close the device
        muteme_driver.close()

    try:
        if args.cmdline:
            muteme_commandline(muteme_driver, args.verbose)
        else:
            update_rate_ms = int(args.update_rate * 1000)
            muteme_ui(muteme_driver, update_rate_ms, args.verbose)
    except KeyboardInterrupt as exception:
        pass
    except Exception as exception:
        cleanup()
        raise exception
    cleanup()


if __name__ == "__main__":
    muteme_main()
