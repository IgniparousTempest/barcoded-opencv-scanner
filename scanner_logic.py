import time
from collections import Counter
from typing import NamedTuple, List, Optional, Tuple, Dict


class _BarcodeTimestamp(NamedTuple):
    timestamp: float
    barcode: bytes


class ScannerLogic(object):
    def __init__(self, set_size: int, required_num: int, set_time: float, cooldown_time: float):
        """
        Handles the scanning logic, returns rhe modal scan above a threshold within some time limit.
        Also applies a cooldown after a successful scan, which allows products to be swapped.
        It uses a monotonic timer, so changes to the system clock do not affect it.

        :param set_size: The number of sequential images to consider.
        :param required_num: The threshold number of images from the set to consider a successful scan.
        :param set_time: The time to keep images in the set in seconds.
        :param cooldown_time: The time to disable the scanner after a successful scan to allow the product to be removed.
        """
        self._set_size = set_size
        self._required_num = required_num
        self._set_time = set_time
        self._cooldown_time = cooldown_time
        self._start_time = 0.0
        self._in_cooldown = False
        self._barcodes: List[_BarcodeTimestamp] = []

    def input(self, barcode: bytes) -> Tuple[Optional[bytes], Dict[bytes, int]]:
        """
        Adds a barcode to the system, returns the barcode if it was deemed to be correct.
        :param barcode: The barcode that was scanned.
        :return: The barcode on a successful scan, None otherwise. A dictionary containing a dict of all detected
        barcodes and their frequency.
        """
        # Enact cooldown
        if self._in_cooldown:
            if time.monotonic() - self._start_time > self._cooldown_time:
                self._in_cooldown = False
            else:
                return None, {}

        # Prune old records
        while len(self._barcodes) > 0:
            if (time.monotonic() - self._barcodes[0].timestamp) > self._set_time:
                del self._barcodes[0]
            else:
                break

        # Add new barcode
        self._barcodes.append(_BarcodeTimestamp(time.monotonic(), barcode))

        # Maintain set size
        while len(self._barcodes) > self._set_size:
            del self._barcodes[0]

        # Return
        barcode_frequencies = Counter([b.barcode for b in self._barcodes])
        most_common = barcode_frequencies.most_common(1)[0]
        if most_common[1] >= self._required_num:
            self._in_cooldown = True
            self._start_time = time.monotonic()
            return most_common[0], dict(barcode_frequencies)
        else:
            return None, dict(barcode_frequencies)
