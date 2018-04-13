from typing import Optional

import requests


class BarcodedAPI(object):
    def __init__(self, ip_address: str, uses_https: bool = False):
        """
        Communicates with the server running Barcoded.
        :param ip_address: The address of the server.
        """
        self._ip_address = ip_address
        self._protocol = 'https' if uses_https else 'http'

    def add_barcode(self, barcode: str) -> Optional[str]:
        """
        Sends a barcode to the barcoded server.
        :param barcode:
        :return: True if successful, false otherwise.
        """
        try:
            url = f"{self._protocol}://{self._ip_address}/api/item/{barcode}"
            result = requests.post(url, data={'quantity_change': 1}).json()
            return result['name']
        except requests.exceptions.ConnectionError:
            return None
