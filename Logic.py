import numpy as np
from collections import Counter

class Logic:
    def __init__(self, Dx, Dy, Dz, Rx, Ry, Rz, dCx, dCy, dCz, X, Y, Z):
        # Initialize any variables if needed
        self.Rx = Rx
        self.Ry = Ry
        self.Rz = Rz
        self.dCx = dCx
        self.dCy = dCy
        self.dCz = dCz
        self.Dx = Dx
        self.Dy = Dy
        self.Dz = Dz
        self.DSum = Dx + Dy + Dz
        self.RSum = Rx + Ry + Rz
        self.dCSum = dCx + dCy + dCz
        self.X = X[-1]
        self.Y = Y[-1]
        self.Z = Z[-1]

        self.P = (self.RSum + self.dCSum - self.DSum) % 3
        self.W = (self.P + self.DSum - self.dCSum - self.RSum) // 3 - 1

        self.PermuteSet = [[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0], [1, 0, 1], [0, 1, 1]]

    #returns all possible solution sets in integer format
    #do not call if self.P == 0
    def solutionSets(self):
        if self.P == 0:
            self.SolutionSet = [[0, 0, 0]]
            return

        self.SolutionSet = []

        # intermediate calculations held constant across all i and Rzx
        i_Ryz = 2 - self.Dy - self.Dz + 2 * self.W + self.dCy + self.dCz + self.Rx + self.Rz
        i_Rxz = - 1 + self.Dz - self.W - self.dCz - self.Ry
        for i in range(self.P * 3 - 3, self.P * 3):
            # try different values of Rzx, given 0 <= Rzx <= Rz
            for Rzx in range(0, self.Rz + 1):
                Rzy = -Rzx + self.Rz
                Ryz = Rzx - i_Ryz + self.PermuteSet[i][1] + self.PermuteSet[i][2]
                Ryx = -Ryz + self.Ry
                Rxz = Ryx + i_Rxz + self.PermuteSet[i][2]
                Rxy = -Rxz + self.Rx
                #constraints/checks
                if Rzy >= 0 and Ryz >= 0 and Ryx >= 0 and Rxz >= 0 and Rxy >= 0 and Rxy + Rxz == self.Rx and Ryx + Ryz == self.Ry and Rzx + Rzy == self.Rz:
                    self.SolutionSet.append(self.PermuteSet[i])
                    break

    #do not call if self.P == 0
    def convertSolutionSetToString(self, x = None, y = None, z = None):
        if x is None and y is None and z is None:
            x, y, z = self.X, self.Y, self.Z
        if self.P == 0:
            return []
        solutionSet = []
        for i in range(len(self.SolutionSet)):
            rowNToSolutionSet = []
            for j in range(3):
                arrayOfTypes = [x, y, z]
                if (self.SolutionSet[i][j] != 0):
                    rowNToSolutionSet.append(arrayOfTypes[j])
            if (rowNToSolutionSet != []):
                solutionSet.append(rowNToSolutionSet)
        return solutionSet

    #returns the common contestants across all combinations/formatted output (MUST BE STRING FORMATTED)
    #do not call if self.P == 0

    def commonFactor(self, solutionSet):
        if self.P == 0:
            return [self.X, self.Y, self.Z]
        if solutionSet == []:
            return [self.X, self.Y, self.Z]
        # Start with the frequency of elements in the first row
        commonCounts = Counter(solutionSet[0])

        for row in solutionSet[1:]:
            commonCounts &= Counter(row)

        commonFactors = list(commonCounts.elements())

        if len(commonFactors) < self.P:
            commonFactors += ['?'] * (self.P - len(commonFactors))

        if self.P < 3:
            commonFactors += [''] * (3 - self.P)

        return commonFactors


