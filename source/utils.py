import psutil


def is_zoom_running():
    for proc in psutil.process_iter():
        if "zoom" in proc.name().lower():
            return True
    return False
