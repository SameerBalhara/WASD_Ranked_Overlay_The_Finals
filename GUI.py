import sys
import threading
import keyboard
from ResolutionDependentData import Resolution
import imageCapture as iC
from imageToText import Text
from Logic import Logic
from mss_singleton import get_sct
from settings import load_settings
import mss
import time
import traceback
import cv2
import numpy as np
import ctypes

from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush, QFontMetrics
from PyQt5.QtWidgets import QApplication, QWidget, QLabel

SUPPORTED = {(1920, 1080), (2560, 1440), (3840, 2160)}

def get_primary_mss_monitor() -> tuple[int, dict]:
    with mss.mss() as sct:
        for idx in range(1, len(sct.monitors)):
            mon = sct.monitors[idx]
            if mon["left"] == 0 and mon["top"] == 0:
                return idx, mon

        # Fallback
        return 1, sct.monitors[1]

def show_native_error(title: str, message: str) -> None:
    flags = 0x10 | 0x40000
    ctypes.windll.user32.MessageBoxW(None, message, title, flags)

initialCoins = None
f8_valid = False

initKeyName = "f8"
scoreKeyName = "tab"

f8Locked = False
f8Lock = threading.Lock()

tabLocked = False
tabReleased = True
tabLock = threading.Lock()

class Bridge(QObject):
    f8_pressed = pyqtSignal()
    tab_pressed = pyqtSignal()

class BoxWidget(QWidget):
    def __init__(self, parent, x, y, width, height, color_name="White", initial_text=""):
        super().__init__(parent)
        self.setGeometry(x, y, width, height)
        self.color = QColor(color_name)
        self.opacity = 0.1

        self.label = QLabel(initial_text, self)
        self.label.setFont(QFont("Consolas", Resolution.boxFontSize, QFont.Bold))
        self.label.setStyleSheet("color: white;")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setGeometry(0, 0, width, height)
        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        fill = QColor(self.color)
        fill.setAlphaF(self.opacity)
        painter.setBrush(QBrush(fill))

        pen = QPen(self.color)
        pen.setWidth(Resolution.boxBorderWidthPx)
        if self.opacity == 0.0:
            pen.setColor(QColor(self.color.red(), self.color.green(), self.color.blue(), 0))
        painter.setPen(pen)

        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)

    def update_color(self, color):
        if color == "Orange":
            color = (238, 117, 7)
        elif color == "Purple":
            color = (143, 72, 238)
        elif color == "Pink":
            color = (241, 59, 174)
        elif color == "White":
            color = (255, 255, 255)

        resolved = QColor(color) if isinstance(color, str) else QColor(*color)
        if self.color != resolved:
            self.color = resolved
            self.update()

    def update_opacity(self, new_opacity: float):
        if self.opacity != new_opacity:
            self.opacity = new_opacity
            self.update()

    def update_text(self, new_text: str):
        self.label.setText("" if new_text is None else str(new_text))


class Overlay(QWidget):
    def __init__(self, bridge):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)

        screen_geo = QApplication.primaryScreen().geometry()

        start_x = screen_geo.width() - Resolution.startXOffsetFromRight
        start_y = screen_geo.height() - Resolution.startYOffsetFromBottom

        box_w, box_h = Resolution.boxW, Resolution.boxH
        spacing = Resolution.gridSpacingPx

        abs_boxes = []
        for row in range(3):
            for col in range(3):
                abs_x = start_x + col * (box_w + spacing)
                abs_y = start_y + row * (box_h + Resolution.spacingFactor * spacing + Resolution.gridRowExtraYPx)
                abs_boxes.append((abs_x, abs_y))

        self.status_font = QFont("Consolas", Resolution.fontSize, QFont.Bold)
        fm = QFontMetrics(self.status_font)

        status_h = int(fm.height() * Resolution.statusHeightMultiplier)
        pad = Resolution.statusPadPx

        min_x = min(x for x, y in abs_boxes)
        min_y = min(y for x, y in abs_boxes)
        max_x = max(x + box_w for x, y in abs_boxes)
        max_y = max(y + box_h for x, y in abs_boxes)

        win_x = min_x
        win_y = min_y - (status_h + pad)

        win_w = (max_x - min_x)
        win_h = (max_y - win_y)

        self.setGeometry(win_x, win_y, win_w, win_h)

        self.status_label = QLabel("Capture Init Coins", self)
        self.status_label.setFont(self.status_font)
        self.status_label.setStyleSheet("color: white;")
        self.status_label.setAlignment(Qt.AlignCenter)

        self.status_label.setGeometry(0, Resolution.statusLabelTopInsetPx, win_w, status_h)

        self.boxes = []
        for (abs_x, abs_y) in abs_boxes:
            local_x = abs_x - win_x
            local_y = abs_y - win_y
            self.boxes.append(BoxWidget(self, local_x, local_y, box_w, box_h, color_name="White", initial_text=""))

        bridge.f8_pressed.connect(self.on_f8_pressed)
        bridge.tab_pressed.connect(self.on_tab_pressed)

        self.show()

    def set_status(self, msg: str):
        self.status_label.setText(msg)

    def update_box(self, index: int, new_text, color="White", opacity=None):
        box = self.boxes[index]
        box.update_text(new_text)
        box.update_color(color)
        box.update_opacity(0.8 if opacity is None else opacity)

    def clear_row(self, row: int):
        for col in range(3):
            self.update_box(row * 3 + col, "", color="White", opacity=0.1)

    def on_f8_pressed(self):
        global f8_valid, initialCoins, f8Locked, initKeyName

        try:
            self.set_status(f"{initKeyName} pressed")

            iC.captureCoins(msDelay=33)

            initCoins = {}
            for i in range(3):
                a = Text.teamColorsOnInitialCoins[i]
                if a is not None:
                    initCoins[a] = Text.initialCoins[i]

            initialCoins = initCoins
            f8_valid = len(initCoins) > 0

            if not f8_valid:
                self.set_status("invalid coin capture")

        except Exception:
            traceback.print_exc()
            self.set_status(f"{initKeyName} error")

        finally:
            with f8Lock:
                f8Locked = False

    def on_tab_pressed(self):
        try:
            if not f8_valid:
                #print("invalid coin capture")
                self.set_status("invalid coin capture")
                return

            global initialCoins
            self.set_status("scoreboard key pressed")

            t0 = time.perf_counter()
            setOfTeamsAlive = self.wipeCheck()
            t1 = time.perf_counter()
            timeToCalculateWipe = (t1 - t0) * 1000

            if timeToCalculateWipe > 33:
                timeToCalculateWipe = 33

            netDelay = 33 - timeToCalculateWipe
            #print("timeToCalculateWipe:", timeToCalculateWipe)
            #print("netDelay:", netDelay)

            iC.takesubImages(msDelay=netDelay)

            for i in range(3):
                t = Text.cvtdText[i]
                a = Text.teamColors[i]

                if a is not None and a in initialCoins and a in setOfTeamsAlive:
                    b = initialCoins[a]
                    l = Logic(
                        int(t[1]), int(t[5]), int(t[9]),
                        int(t[2]), int(t[6]), int(t[10]),
                        int(b[0]) - int(t[3]),
                        int(b[1]) - int(t[7]),
                        int(b[2]) - int(t[11]),
                        t[0], t[4], t[8]
                    )
                    l.solutionSets()
                    c = l.convertSolutionSetToString()
                    d = l.commonFactor(c)

                    for col in range(3):
                        self.update_box(i * 3 + col, d[col], color=a)
                    #print(d)

                else:
                    self.clear_row(i)

        except Exception:
            traceback.print_exc()
        finally:
            self.placeHolderFunction()

    def placeHolderFunction(self):
        global tabLocked, tabReleased
        with tabLock:
            tabLocked = False

    def wipeCheck(self):
        #return {'Pink', 'Purple', 'Orange'}
        x1, x2 = Resolution.wipeCrop[0], Resolution.wipeCrop[1]
        y1, y2 = Resolution.wipeCrop[2], Resolution.wipeCrop[3]

        roi = {"left": x1, "top": y1, "width": x2 - x1, "height": y2 - y1}
        sct = get_sct()
        img = sct.grab(roi)
        scene = np.array(img)[:, :, :3]

        aliveTeams = set()

        for x, y in Resolution.wipeCoordinates:
            average_color = cv2.mean(scene[x:y])[:3]
            b, g, r = average_color
            sample = [[int(r), int(g), int(b)]]
            colorString = str((Resolution.color_clf.predict(sample)[0]))
            confidenceLevel = float(max(Resolution.color_clf.predict_proba(sample)[0]))
            if confidenceLevel > 0.9:
                aliveTeams.add(colorString)
            #print((colorString, confidenceLevel))

        return aliveTeams


def keyboard_thread(bridge, keybinds):
    init_key = keybinds["initialScreenshot"]
    score_key = keybinds["scoreboard"]

    def f8_press(e):
        global f8Locked
        with f8Lock:
            if f8Locked:
                return
            f8Locked = True
        bridge.f8_pressed.emit()

    keyboard.on_press_key(init_key, f8_press)

    def tab_press(e):
        global tabLocked, tabReleased
        with tabLock:
            if tabLocked or not tabReleased:
                return
            tabLocked = True
            tabReleased = False
        bridge.tab_pressed.emit()

    def tab_release(e):
        global tabReleased
        with tabLock:
            tabReleased = True

    keyboard.on_press_key(score_key, tab_press)
    keyboard.on_release_key(score_key, tab_release)
    keyboard.wait()

def main():
    settings = load_settings()
    keybinds = settings["keybinds"]
    global initKeyName, scoreKeyName
    initKeyName = str(keybinds.get("initialScreenshot", "f8"))
    scoreKeyName = str(keybinds.get("scoreboard", "tab"))

    monitorIndex, primary_mon = get_primary_mss_monitor()
    w, h = primary_mon["width"], primary_mon["height"]
    #print("Primary MSS index:", monitorIndex, "Resolution:", (w, h))

    if (w, h) not in SUPPORTED:
        show_native_error(
            "Invalid Monitor Resolution",
            f"Detected: {w} x {h}\n\n"
            "Supported resolutions:\n"
            "• 1920 x 1080\n"
            "• 2560 x 1440\n"
            "• 3840 x 2160\n\n"
            "Fix your display settings and relaunch."
        )
        sys.exit(1)

    res = Resolution()
    res.init((w, h))

    app = QApplication(sys.argv)
    bridge = Bridge()
    overlay = Overlay(bridge)

    t = threading.Thread(target = keyboard_thread, args = (bridge, keybinds), daemon = True)
    t.start()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
