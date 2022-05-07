import threading
import msvcrt

from logger import write_log


class KeyInput:
    def __init__(self) -> None:
        self.__buffer: list = [bytes]
        self.__buffer_mutex: threading.Lock = threading.Lock()

        self.__thread: threading.Thread = threading.Thread(target=self.__on_thread)
        self.__thread.start()

    def terminate(self) -> None:
        thread = self.__thread
        self.__thread = None
        thread.join()

    def __on_thread(self) -> None:        
        while self.__thread is not None:
            key = self.__impl_get_key_windows()
            if key == b'':
                continue

            self.__buffer_mutex.acquire()
            self.__buffer.append(key)
            self.__buffer_mutex.release()

    def get_key(self) -> bytes:
        self.__buffer_mutex.acquire()
        if len(self.__buffer) == 0:
            result = -1
        else:
            result = self.__buffer[0]
            self.__buffer = self.__buffer[1:] if len(self.__buffer) > 1 else []

        self.__buffer_mutex.release()
        return result

    def get_key_buffer(self) -> list[bytes]:
        self.__buffer_mutex.acquire()

        result = self.__buffer
        self.__buffer = []

        self.__buffer_mutex.release()
        return result

    def __impl_get_key_windows(self) -> bytes:
        if msvcrt.kbhit():
            return msvcrt.getch()

        return b''
