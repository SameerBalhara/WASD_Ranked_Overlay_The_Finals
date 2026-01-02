import sys
import threading
import keyboard
from ResolutionDependentData import Resolution
import imageCapture as iC
from imageToText import Text
from Logic import Logic
import time
import traceback
import mss
import cv2
import numpy as np

from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush, QFontMetrics
from PyQt5.QtWidgets import QApplication, QWidget, QLabel

initialCoins = None
f8_valid = False
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
        pen.setWidth(2)
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
        spacing = 30

        abs_boxes = []
        for row in range(3):
            for col in range(3):
                abs_x = start_x + col * (box_w + spacing)
                abs_y = start_y + row * (box_h + Resolution.spacingFactor * spacing + 5)
                abs_boxes.append((abs_x, abs_y))

        self.status_font = QFont("Consolas", Resolution.boxFontSize, QFont.Bold)
        fm = QFontMetrics(self.status_font)

        status_h = int(fm.height() * 1.35)
        pad = 6

        min_x = min(x for x, y in abs_boxes)
        min_y = min(y for x, y in abs_boxes)
        max_x = max(x + box_w for x, y in abs_boxes)
        max_y = max(y + box_h for x, y in abs_boxes)

        win_x = min_x
        win_y = min_y - (status_h + pad)

        win_w = (max_x - min_x)
        win_h = (max_y - win_y)

        self.setGeometry(win_x, win_y, win_w, win_h)

        self.status_label = QLabel("Waiting for Input", self)
        self.status_label.setFont(self.status_font)
        self.status_label.setStyleSheet("color: white;")
        self.status_label.setAlignment(Qt.AlignCenter)

        self.status_label.setGeometry(0, pad // 2, win_w, status_h)

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
        global f8_valid, initialCoins

        self.set_status("f8 pressed")

        iC.captureCoins(msDelay=33)

        initCoins = {}
        for i in range(3):
            a = Text.teamColorsOnInitialCoins[i]
            if a is not None:
                initCoins[a] = Text.initialCoins[i]

        initialCoins = initCoins
        f8_valid = len(initCoins) > 0
        print(initialCoins)

        if not f8_valid:
            self.set_status("f8 invalid")

    def on_tab_pressed(self):
        try:
            if not f8_valid:
                print("f8 not valid")
                self.set_status("f8 not valid")
                return

            global initialCoins
            self.set_status("tab pressed")

            t0 = time.perf_counter()
            setOfTeamsAlive = self.wipeCheck()
            t1 = time.perf_counter()
            timeToCalculateWipe = (t1 - t0) * 1000

            if timeToCalculateWipe > 33:
                timeToCalculateWipe = 33

            netDelay = 33 - timeToCalculateWipe
            print("timeToCalculateWipe:", timeToCalculateWipe)
            print("netDelay:", netDelay)

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

                    print(d)

                elif a is not None and a not in initialCoins:
                    self.set_status("f8 not updated before round start")
                    self.clear_row(i)
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
            tabReleased = True

    def wipeCheck(self):
        #return {'Pink', 'Purple', 'Orange'}
        x1, x2 = 182, 195
        y1, y2 = 125, 450
        coordinates = [(0, 13), (80, 93), (235, 248), (312, 325)]

        roi = {"left": x1, "top": y1, "width": x2 - x1, "height": y2 - y1}
        with mss.mss() as sct:
            img = sct.grab(roi)
            scene = np.array(img)[:, :, :3]

        aliveTeams = set()

        for x, y in coordinates:
            average_color = cv2.mean(scene[x:y])[:3]
            b, g, r = average_color
            sample = [[int(r), int(g), int(b)]]
            colorString = str((Resolution.color_clf.predict(sample)[0]))
            confidenceLevel = float(max(Resolution.color_clf.predict_proba(sample)[0]))
            if confidenceLevel > 0.9:
                aliveTeams.add(colorString)
            print((colorString, confidenceLevel))

        return aliveTeams


def keyboard_thread(bridge):
    keyboard.add_hotkey("f8", bridge.f8_pressed.emit)

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

    keyboard.on_press_key("tab", tab_press)
    keyboard.on_release_key("tab", tab_release)
    keyboard.wait()


def main():
    res = Resolution()
    res.init((3840, 2160))

    app = QApplication(sys.argv)
    bridge = Bridge()
    overlay = Overlay(bridge)

    t = threading.Thread(target=keyboard_thread, args=(bridge,), daemon=True)
    t.start()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
