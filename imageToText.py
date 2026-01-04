from ResolutionDependentData import Resolution
import cv2
import numpy as np

#WARNING: class should only ever be accessed after ResolutionDependentData is initialized
class Text():

    cvtdText = None
    initialCoins = None

    #one entry per team
    expectedDataFormat = [False] * 3
    teamColors = [None] * 3
    validCoinStates = [False] * 3

#assume another file takes the minimally sized subimages and passes them as a numpy array
#format will be teamA Left to Right, Top Down (easier for modulo requirements)

    #numpyData is B/W and binarized
    #colorSamples is the 0th, 12th, 24th images of the 36 images, in color
    @classmethod
    def cvtImageToText_36(cls, numpyData, colorSamples):
        cls.ref_stack = Resolution.ref_stack
        cls.ref_labels = Resolution.ref_labels
        cls.maxHammingDistance = Resolution.maxHammingDistance
        cls.color_clf = Resolution.color_clf

        cvtdText = []

        for subimage in numpyData:
            HDs = np.count_nonzero(cls.ref_stack != subimage , axis=(1, 2))
            best_idx = int(np.argmin(HDs))
            best_hd = int(HDs[best_idx])
            label = cls.ref_labels[best_idx]
            cvtdText.append(label)

        cls.cvtdText = [cvtdText[0:12], cvtdText[12:24], cvtdText[24:36]]
        cls.expectedDataFormat = [True, True, True]

        potentialContestants = ['_H', '_M', '_L']
        for i in range(36):
            if i % 4 == 0:
                if cvtdText[i] not in potentialContestants:
                    cls.expectedDataFormat[i // 12] = False
            else:
                if not cvtdText[i].isdigit():
                    cls.expectedDataFormat[i // 12] = False

        for i in range(3):
            if cls.expectedDataFormat[i]:
                average_color = cv2.mean(colorSamples[i])[:3]
                b, g, r = average_color
                sample = [[int(r), int(g), int(b)]]
                colorString = str((cls.color_clf.predict(sample)[0]))
                cls.teamColors[i] = colorString
            else:
                cls.teamColors[i] = None

    #Produces correspondence between team colors and valid coin states. Only when all three players
    # on a given team are connected to game will the initial coin states be valid. Index positions
    # link each team color to the appropriate coin counts. Other methods should check for
    # validCoinStates first, passing along flags to indicate that index/row of data is invalid.
    # If a team color is not None, then initialCoins are valid to be used in Logic.py
    @classmethod
    def convertCoinImages(cls, numpyData, colorSamples):
        cls.ref_stack = Resolution.ref_stack
        cls.ref_labels = Resolution.ref_labels
        cls.maxHammingDistance = Resolution.maxHammingDistance

        cvtdText = []
        for subimage in numpyData:
            HDs = np.count_nonzero(cls.ref_stack != subimage , axis=(1, 2))
            best_idx = int(np.argmin(HDs))
            cvtdText.append(cls.ref_labels[best_idx])

        cls.initialCoins = [cvtdText[0:3], cvtdText[3:6], cvtdText[6:9]]
        cls.teamColorsOnInitialCoins = [None, None, None]
        cls.validCoinStates = [True, True, True]

        for i in range(9):
            if not cvtdText[i].isdigit():
                cls.validCoinStates[i // 3] = False

        for i in range(3):
            if cls.validCoinStates[i]:
                average_color = cv2.mean(colorSamples[i])[:3]
                b, g, r = average_color
                sample = [[int(r), int(g), int(b)]]
                colorString = str((Resolution.color_clf.predict(sample)[0]))
                cls.teamColorsOnInitialCoins[i] = colorString


