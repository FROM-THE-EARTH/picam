from __future__ import annotations
import datetime
import os
import time
import threading
import typing as t

import picamera
import RPI.GPIO as gpio


def _get_timestamp(
    tag: t.Optional[str] = None,
    suffix: t.Optional[str] = None,
) -> str:
    timestamp = datetime.datetime.now().strftime("%y%m%d-%H:%M:%S")
    if tag is not None and len(tag):
        timestamp = "-".join(tag, timestamp)
    if suffix is not None and len(suffix):
        timestamp = ".".join(timestamp, suffix)
    return timestamp


_video_formats = {
    "h264",
    "mjpeg",
    "yuv",
    "rgb",
    "rgba",
    "bgr",
    "bgra",
}


def _isvalid_video_format(path: str) -> bool:
    ext = os.path.splitext(path)[1]
    if not len(ext):
        return False
    return ext[1:] in _video_formats


class IORecorder:

    def __init__(
        self,
        pin_input: int,
        fname: t.Optional[str] = None,
        resolution: t.Tuple = (640, 480)
    ) -> None:
        if fname is None:
            fname = _get_timestamp("mov", "h264")
        elif _isvalid_video_format(fname):
            raise ValueError(f"'{fname}' has an invalid extension.")

        self._camera = picamera.PiCamera()
        self._camera.resolution = resolution
        self._fname = fname
        self._pin_input = pin_input
        self._thread: t.Optional[threading.Thread] = None

        gpio.setup(self._pin_input, gpio.IN)

    @property
    def is_high(self) -> bool:
        return bool(gpio.input(self._pin_input))

    def _start_record(
        self,
        interval: float = 1.,
        timeout: float = -1,
        start_level: bool = True,
    ) -> None:
        if timeout <= 0:
            timeout = float("inf")

        if start_level:
            # high --> recording
            # low  --> not recording
            should_stop = lambda: not self.is_high
        else:
            # high --> not recording
            # low  --> recording
            should_stop = lambda: self.is_high

        # Wait for the level to be either expected.
        while should_stop():
            pass

        # Start recording
        self._camera.start_recording(self._fname)
        time_init = time.time()
        try:
            while not should_stop():
                if 0 < timeout <= time.time() - time_init:
                    break
                self._camera.wait_recording(timeout=interval)
        finally:
            self._camera.stop_recording()

    def start_record(
        self,
        interval: float = 1.,
        timeout: float = -1,
        start_level: bool = True,
    ) -> IORecorder:
        self._thread = threading.Thread(
            target=self._start_record,
            args=(interval, timeout, start_level),
        )
        self._thread.start()
        return self

    def stop_record(self, timeout: float = -1) -> None:
        if self._thread is None:
            return

        self._thread.join(timeout=timeout)
        self._thread = None

    def __enter__(self) -> IORecorder:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.stop_record()
