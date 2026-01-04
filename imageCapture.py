from ResolutionDependentData import Resolution
from imageToText import Text
import cv2
import time
import mss
import numpy as np

#WARNING: class should only ever be accessed after ResolutionDependentData is initialized
def takesubImages(msDelay = 0, monIndex = 0):
    #waits for msDelay ms before image capture
    t0 = time.perf_counter()
    target = t0 + msDelay / 1000
    while True:
        remaining = target - time.perf_counter()
        if remaining <= 0:
            break
        time.sleep(min(remaining, 0.002))

    pixelLocations = Resolution.absPxls
    scene = None

    with mss.mss() as sct:
        monitor = sct.monitors[monIndex]
        scene = np.array(sct.grab(monitor))[:, :, :3]

    if scene is not None:
        BinarizedImages = []
        colorSamples = []

        for i in range(36):
            coord = pixelLocations[i]
            tl, br = coord[0], coord[1]
            subimage = scene[tl[1]:br[1], tl[0]:br[0]]

            if i % 12 == 0:
                colorSamples.append(subimage)

            gray = cv2.cvtColor(subimage, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY)
            BinarizedImages.append(binary)

        t = Text()
        t.cvtImageToText_36(BinarizedImages, colorSamples)

def captureCoins(msDelay = 0, monIndex = 0):
    #waits for msDelay ms before image capture
    t0 = time.perf_counter()
    target = t0 + msDelay / 1000
    while True:
        remaining = target - time.perf_counter()
        if remaining <= 0:
            break
        time.sleep(min(remaining, 0.002))

    pixelLocations = Resolution.absPxls
    scene = None

    with mss.mss() as sct:
        monitor = sct.monitors[monIndex]
        scene = np.array(sct.grab(monitor))[:, :, :3]

    if scene is not None:
        BinarizedImages = []
        colorSamples = []

        for i in range(36):
            if (i - 3) % 4 != 0:
                continue
            coord = pixelLocations[i]
            tl, br = coord[0], coord[1]
            subimage = scene[tl[1]:br[1], tl[0]:br[0]]

            if (i - 3) % 12 == 0:
                colorSamples.append(subimage)

            gray = cv2.cvtColor(subimage, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY)
            BinarizedImages.append(binary)

        t = Text()
        t.convertCoinImages(BinarizedImages, colorSamples)

