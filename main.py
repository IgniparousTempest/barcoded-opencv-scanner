import argparse as aparse
import sys
from typing import List, Tuple

import cv2
import numpy

import zbar

import feedback
from barcoded_api import BarcodedAPI
from scanner_logic import ScannerLogic


def print_camera_config(cap: cv2.VideoCapture):
    test = cap.get(cv2.CAP_PROP_POS_MSEC)
    ratio = cap.get(cv2.CAP_PROP_POS_AVI_RATIO)
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    brightness = cap.get(cv2.CAP_PROP_BRIGHTNESS)
    contrast = cap.get(cv2.CAP_PROP_CONTRAST)
    saturation = cap.get(cv2.CAP_PROP_SATURATION)
    hue = cap.get(cv2.CAP_PROP_HUE)
    gain = cap.get(cv2.CAP_PROP_GAIN)
    exposure = cap.get(cv2.CAP_PROP_EXPOSURE)
    print("0.  Position:   ", test)
    print("2.  Ratio:      ", ratio)
    print("3.  Width:      ", width)
    print("4.  Height:     ", height)
    print("5.  Frame Rate: ", frame_rate)
    print("10. Brightness: ", brightness)
    print("11. Contrast:   ", contrast)
    print("12. Saturation: ", saturation)
    print("13. Hue:        ", hue)
    print("14. Gain:       ", gain)
    print("15. Exposure:   ", exposure)


def read_barcode(scanner: zbar.Scanner, image: numpy.ndarray) -> List[zbar.Symbol]:
    """
    Extracts the barcode from a colour image using zbar.
    :param scanner: The zbar scanner.
    :param image: The colour image from the webcam.
    :return: A list of zbar symbols.
    """
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    return scanner.scan(gray_image)


def draw_barcode(image: numpy.ndarray, positions: List[Tuple[int, int]]):
    """
    Draws the detected start, middle, end guards.
    :param image: The image to draw to.
    :param positions: The detected positions of the guards.
    """
    for point in positions:
        cv2.rectangle(image, (point[0] - 2, point[0] - 2), (point[0] + 2, point[0] + 2), (0, 255, 0), 1)


def main(ip_address: str, scanner_logic: ScannerLogic, show_video=False):
    cap = cv2.VideoCapture(0)
    scanner = zbar.Scanner()
    api = BarcodedAPI(ip_address)
    while True:
        ret, img = cap.read()
        if img is None:
            print("Failed to get camera", file=sys.stderr)
            sys.exit(1)

        results = read_barcode(scanner, img)
        for result in results:
            # TODO: Incorporate the result.quality into the scanner logic?
            barcode, others = scanner_logic.input(result.data)
            if barcode is not None:
                print(barcode, others)
                feedback.play_sound()
                result = api.add_barcode(barcode.decode("utf-8"))

                if result is not None:
                    print(result)
                else:
                    print("Could not send barcode to server.", file=sys.stderr)

        if show_video:
            for res in results:
                draw_barcode(img, res.position)
            cv2.imshow("input", img)

        key = cv2.waitKey(10)
        if key == 27:
            break

    cv2.destroyAllWindows()
    cv2.VideoCapture(0).release()


if __name__ == '__main__':
    parser = aparse.ArgumentParser(formatter_class=aparse.ArgumentDefaultsHelpFormatter,
                                   description='Runs a client for a barcoded server, uses the webcam to scan barcodes.')
    parser.add_argument('ip_address', metavar='IP', type=str, help='The IP address of the barcoded server.')
    parser.add_argument('port', metavar='PORT', type=int, nargs='?', default=41040,
                        help='The port of the barcoded server.')
    parser.add_argument('set_size', metavar='S', type=int, nargs='?', default=10,
                        help='The number of the most recent barcodes to consider.')
    parser.add_argument('required_num', metavar='N', type=int, nargs='?', default=7,
                        help='The number of barcodes to match in the set, to be considered a successful match.')
    parser.add_argument('barcode_lifetime', metavar='L', type=float, nargs='?', default=2.0,
                        help='The time to keep barcodes in the set.')
    parser.add_argument('cooldown_time', metavar='C', type=float, nargs='?', default=2.0,
                        help='The time the scanner goes into cooldown for after a successful scan.')
    parser.add_argument('--show-video', action='store_true', help='Displays the video feed from the camera.')

    args = parser.parse_args()
    scanner_logic = ScannerLogic(args.set_size, args.required_num, args.barcode_lifetime, args.cooldown_time)
    main(args.ip_address + ':' + str(args.port), scanner_logic, args.show_video)
