import threading

_lock = threading.Lock()


class RegistrationLock:
    def __enter__(self):
        _lock.acquire()

    def __exit__(self, *args):
        _lock.release()